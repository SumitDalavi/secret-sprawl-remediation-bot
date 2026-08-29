import os
import re
import tempfile
import subprocess
import json
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

# ---------------------------------------------------------------------------
# In-process regex fallback — covers common secret patterns without requiring
# the gitleaks binary. Used when gitleaks is unavailable or scan fails.
# ---------------------------------------------------------------------------
FALLBACK_PATTERNS = [
    # AWS Access Key IDs
    ("aws", re.compile(r"AKIA[0-9A-Z]{16}")),
    # Generic API keys: api_key=<long value>
    ("generic", re.compile(r"(?i)api[_-]?key\s*[=:]\s*['\"]?([A-Za-z0-9_\-]{20,})['\"]?")),
    # GitHub PATs (classic and fine-grained)
    ("github", re.compile(r"ghp_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{82}")),
    # Generic high-entropy secrets attached to common env var names
    ("generic", re.compile(r"(?i)(?:secret|password|passwd|token|private_key)\s*[=:]\s*['\"]?([A-Za-z0-9+/]{32,})['\"]?")),
]


class GitleaksScanner:
    def _scan_with_regex(self, commit_diff: str) -> list:
        """In-process fallback: regex-based secret detection."""
        findings = []
        for line_no, line in enumerate(commit_diff.splitlines(), start=1):
            if not line.startswith("+"):
                continue
            for provider, pattern in FALLBACK_PATTERNS:
                match = pattern.search(line)
                if match:
                    findings.append({
                        "line_number": line_no,
                        "line_content": line,
                        "provider": provider,
                        "secret_match": match.group(0),
                    })
                    break  # one finding per line
        return findings

    def scan_commit(self, commit_diff: str) -> list:
        """
        Primary: try gitleaks binary for comprehensive detection.
        Fallback: in-process regex patterns — deterministic, no binary required.
        """
        findings = []
        gitleaks_ok = False

        with tempfile.NamedTemporaryFile(
            delete=False, suffix=".diff", mode="w", encoding="utf-8"
        ) as temp_file:
            temp_file.write(commit_diff)
            temp_file_path = temp_file.name

        try:
            report_path = temp_file_path + ".json"
            result = subprocess.run(
                [
                    "gitleaks", "detect",
                    "--source", temp_file_path,
                    "--report-format", "json",
                    "--report-path", report_path,
                    "--no-git",
                ],
                capture_output=True,
                text=True,
            )
            if os.path.exists(report_path):
                with open(report_path, "r", encoding="utf-8") as rf:
                    report_data = json.load(rf)
                for finding in report_data:
                    findings.append({
                        "line_number": finding.get("StartLine", 0),
                        "line_content": finding.get("Match", ""),
                        "provider": finding.get("RuleID", "generic").lower(),
                        "secret_match": finding.get("Secret", ""),
                    })
                os.remove(report_path)
                gitleaks_ok = True
        except FileNotFoundError:
            pass  # gitleaks not installed — fall through to regex
        except Exception as e:
            print(f"gitleaks scan error: {e}")
        finally:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

        if not gitleaks_ok:
            findings = self._scan_with_regex(commit_diff)

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
