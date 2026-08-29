# Runbook — secret-sprawl-remediation-bot
> Last updated: 2026-08-29

## Prerequisites

| Tool | Version | Notes |
|---|---|---|
| Python | 3.10+ | `python --version` |
| pip | Any | Via venv |
| gitleaks | Optional | Fallback regex runs if not installed. [Install](https://github.com/gitleaks/gitleaks#installing) |
| Docker | Optional | For real Redis only |

## Quick Start

```bash
# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate      # Windows
# source venv/bin/activate  # Linux/macOS

# Install dependencies
pip install -r requirements.txt

# (Optional) Start shared Redis for dedup caching
# docker compose -f ../../docker-compose.infra.yml up -d redis

# Start the FastAPI webhook server
uvicorn src.bot:app --host 0.0.0.0 --port 8000 --reload
```

## Run Tests

```bash
# Using the project venv:
venv\Scripts\pytest tests\test_all.py -v
```

Expected output:
```
tests/test_all.py::test_root_bot PASSED
tests/test_all.py::test_root_bot_error PASSED
tests/test_all.py::test_root_bot_load_error PASSED
tests/test_all.py::test_src_bot PASSED
tests/test_all.py::test_src_bot_no_secrets PASSED
tests/test_all.py::test_jira_ticket PASSED
tests/test_all.py::test_slack_alert PASSED
tests/test_all.py::test_github_revoke PASSED
tests/test_all.py::test_aws_revoke PASSED
tests/test_all.py::test_gcp_revoke PASSED

10 passed in 5.17s
```

> **Note:** Tests mock all external dependencies (boto3, googleapiclient, httpx). No credentials required.

## Batch Mode — Process a Gitleaks Report

```bash
# Start the mock API server in one terminal:
python mock_api/server.py

# In another terminal, run the bot against a report:
python bot.py data/mock_gitleaks_report.json
```

## Send a Test Webhook

```bash
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "repository": "my-app",
    "diff": "+++ b/config.py\n+ AWS_KEY = '\''AKIAIOSFODNN7EXAMPLE'\''\n+ api_key='\''12345678901234567890123'\''}"
  }'
```

Expected response (regex fallback when gitleaks not installed):
```json
{ "secrets_found": 2, "tickets_created": ["SEC-123", null] }
```

## Environment Variables

| Variable | Default | Purpose |
|---|---|---|
| `REDIS_URL` | `redis://localhost:6379/0` | Dedup cache. Gracefully skipped if unreachable |
| `JIRA_URL` | unset | Jira base URL (e.g., `https://company.atlassian.net`) |
| `JIRA_USER` | unset | Jira username/email |
| `JIRA_TOKEN` | unset | Jira API token |
| `SLACK_WEBHOOK_URL` | unset | Slack incoming webhook URL |
| `GITHUB_TOKEN` | unset | GitHub token for PAT revocation |

## Common Failure Modes

| Symptom | Cause | Fix |
|---|---|---|
| `secrets_found: 0` on a diff with secrets | `gitleaks` not in PATH AND regex didn't match | Check regex patterns in `FALLBACK_PATTERNS`; test with `+AWS_KEY = 'AKIAIOSFODNN7EXAMPLE'` |
| `redis.exceptions.ConnectionError` | Redis not running | Normal — dedup is skipped gracefully. Start Redis if needed. |
| `test_src_bot FAILED: assert 2 == 0` | Old code without regex fallback | Pull latest `src/bot.py` (fix applied 2026-08-29) |
| `ModuleNotFoundError: boto3` | Not installed | `pip install -r requirements.txt` in venv |
