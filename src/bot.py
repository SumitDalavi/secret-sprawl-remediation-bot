import re
import uuid

class SecretScanner:
    def __init__(self):
        # Basic regex for high entropy strings that look like keys
        self.secret_patterns = [
            re.compile(r'(?i)(api_key|apikey|secret)[=":\s]+([a-zA-Z0-9]{32,})'),
            re.compile(r'AKIA[0-9A-Z]{16}') # Mock AWS key
        ]

    def scan_commit(self, commit_diff):
        """Scans a git commit diff for secrets."""
        findings = []
        lines = commit_diff.split('\n')
        for i, line in enumerate(lines):
            for pattern in self.secret_patterns:
                if pattern.search(line):
                    findings.append({
                        "line_number": i + 1,
                        "line_content": line.strip()
                    })
        return findings

class JiraClientMock:
    def create_ticket(self, finding, repo_name):
        """Simulates creating a Jira ticket for remediation."""
        ticket_id = f"SEC-{str(uuid.uuid4())[:8].upper()}"
        return {
            "ticket_id": ticket_id,
            "status": "Created",
            "summary": f"Secret exposed in {repo_name}"
        }

class RemediationBot:
    def __init__(self):
        self.scanner = SecretScanner()
        self.jira = JiraClientMock()

    def process_webhook(self, payload):
        """Processes a mock webhook payload from GitHub/GitLab."""
        repo = payload.get("repository", "unknown")
        diff = payload.get("diff", "")
        
        findings = self.scanner.scan_commit(diff)
        tickets = []
        
        for finding in findings:
            ticket = self.jira.create_ticket(finding, repo)
            tickets.append(ticket)
            
        return {
            "secrets_found": len(findings),
            "tickets_created": tickets
        }

if __name__ == "__main__":
    bot = RemediationBot()
    mock_payload = {
        "repository": "my-app",
        "diff": "+++ b/config.py\n+ AWS_KEY = 'AKIAIOSFODNN7EXAMPLE'"
    }
    result = bot.process_webhook(mock_payload)
    print(f"Bot execution complete: {result}")
