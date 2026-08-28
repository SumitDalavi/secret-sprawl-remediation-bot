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

import tempfile
import subprocess
import json

class GitleaksScanner:
    def scan_commit(self, commit_diff: str):
        findings = []
        # Write diff to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".diff", mode="w", encoding="utf-8") as temp_file:
            temp_file.write(commit_diff)
            temp_file_path = temp_file.name

        try:
            # Run gitleaks detect on the diff file
            # gitleaks detect --source temp.diff --report-format json --report-path report.json --no-git
            report_path = temp_file_path + ".json"
            subprocess.run([
                "gitleaks", "detect",
                "--source", temp_file_path,
                "--report-format", "json",
                "--report-path", report_path,
                "--no-git"
            ], capture_output=True, text=True)

            if os.path.exists(report_path):
                with open(report_path, "r", encoding="utf-8") as rf:
                    report_data = json.load(rf)
                
                for finding in report_data:
                    findings.append({
                        "line_number": finding.get("StartLine", 0),
                        "line_content": finding.get("Match", ""),
                        "provider": finding.get("RuleID", "generic").lower(),
                        "secret_match": finding.get("Secret", "")
                    })
                os.remove(report_path)
        except Exception as e:
            print(f"Failed to run gitleaks: {e}")
        finally:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

        return findings

scanner = GitleaksScanner()

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
