import os
import re
from fastapi import FastAPI, Request
from pydantic import BaseModel
import redis

from jira.ticket import create_remediation_ticket
from notifications.slack import send_remediation_alert
from revocations.github import revoke_token
from revocations.aws import deactivate_access_key

app = FastAPI(title="Secret Sprawl Remediation Bot API")

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
try:
    redis_client = redis.Redis.from_url(REDIS_URL, socket_timeout=1, socket_connect_timeout=1)
except Exception:
    redis_client = None

class SecretScanner:
    def __init__(self):
        self.secret_patterns = [
            (re.compile(r'(?i)(api_key|apikey|secret)[=":\s]+([a-zA-Z0-9]{32,})'), "generic"),
            (re.compile(r'AKIA[0-9A-Z]{16}'), "aws"),
            (re.compile(r'ghp_[a-zA-Z0-9]{36}'), "github")
        ]

    def scan_commit(self, commit_diff: str):
        findings = []
        lines = commit_diff.split('\n')
        for i, line in enumerate(lines):
            for pattern, provider in self.secret_patterns:
                match = pattern.search(line)
                if match:
                    findings.append({
                        "line_number": i + 1,
                        "line_content": line.strip(),
                        "provider": provider,
                        "secret_match": match.group(0)
                    })
        return findings

scanner = SecretScanner()

@app.post("/webhook")
async def process_webhook(request: Request):
    payload = await request.json()
    repo = payload.get("repository", "unknown")
    diff = payload.get("diff", "")
    
    findings = scanner.scan_commit(diff)
    tickets = []
    
    for finding in findings:
        secret = finding["secret_match"]
        provider = finding["provider"]
        
        # Check state to prevent duplicate processing
        cache_key = f"secret:{secret}"
        if redis_client:
            try:
                if redis_client.get(cache_key):
                    continue  # Already processed
                redis_client.setex(cache_key, 86400 * 30, "processed") # 30 days
            except Exception:
                pass

        # Attempt revocation
        revocation_result = None
        if provider == "github":
            revocation_result = revoke_token(secret)
        elif provider == "aws":
            # Extract access key ID (simplistic)
            match = re.search(r'AKIA[0-9A-Z]{16}', secret)
            if match:
                revocation_result = deactivate_access_key(match.group(0))

        # Create Jira Ticket
        res_list = [revocation_result] if revocation_result else []
        ticket_id = create_remediation_ticket([finding], res_list)
        
        # Send Slack Alert
        send_remediation_alert([finding], res_list)
        
        tickets.append(ticket_id)
        
    return {
        "secrets_found": len(findings),
        "tickets_created": tickets
    }
