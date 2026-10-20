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

## Release Runbook

### Triggering a New Release
Releases are automated via GitHub Actions (`.github/workflows/release.yml`) and trigger whenever a semantic version tag is pushed:

```bash
# 1. Ensure master is clean and up-to-date
git checkout master
git pull origin master

# 2. Tag the release
git tag -a v0.2.0 -m "Release v0.2.0"

# 3. Push the tag to trigger the pipeline
git push origin v0.2.0
```

### Release Pipeline Stages
1. **Test Verification:** Runs project test suite gates prior to container build.
2. **Container Image Build:** Builds the production container image (`ghcr.io/sumitdalavi/secret-sprawl-remediation-bot:<tag>`).
3. **Trivy Vulnerability Scan:** Scans the built container for CRITICAL and HIGH CVEs via Aqua Security Trivy.
4. **Anchore Syft SBOM Generation:** Creates an SPDX JSON Software Bill of Materials (`sbom.spdx.json`).
5. **GitHub Release Publishing:** Creates the release with auto-generated release notes and attaches `sbom.spdx.json`.

### Verifying the Release
```bash
# Check workflow run status
gh run list --workflow=release.yml --repo SumitDalavi/secret-sprawl-remediation-bot

# Inspect the published release and attached assets
gh release view v0.1.0 --repo SumitDalavi/secret-sprawl-remediation-bot

# Download and inspect the SBOM
gh release download v0.1.0 --repo SumitDalavi/secret-sprawl-remediation-bot -p "sbom.spdx.json"
cat sbom.spdx.json | jq .spdxVersion
```

### Release Failure Modes
| Symptom | Cause | Resolution |
|---|---|---|
| `Unable to resolve action ... unable to find version` | Pinned action tag missing or upstream tag modified | Pin action to a verified release tag (`@v0.36.0`) or commit SHA |
| `invalid reference format: repository name must be lowercase` | Container repository owner contains uppercase characters | Lowercase the repository owner before tagging (`tr '[:upper:]' '[:lower:]'`) |
| `File not found: sbom.spdx.json` during release step | SBOM action configured with `artifact-name` instead of `output-file` | Ensure `output-file: sbom.spdx.json` is set in Anchore action |

## Operations & Diagnostics Guide (v0.2.0)

### Mode Verification & Diagnostics
Inspect the active execution mode and backing provider status via the health endpoint:
```bash
# Check runtime mode and adapter status
curl -s http://localhost:8080/health | jq .
# Expected output when running without keys:
# {"status": "ok", "mode": {"database": "mock", "ai": "mock", "cache": "mock"}}
```

### Running in Mock Mode (Tier 1)
Start the service with zero external dependencies:
```bash
cp .env.example .env
# Start service without modifying .env
npm start || python main.py || go run .
```

### Running with Live Credentials (Tier 2 / 3)
Populate target credentials in `.env` and restart:
```bash
# Verify live upgrade via health check
curl -s http://localhost:8080/health | jq .mode
```

### Pulling Pre-Built OCI Image
```bash
docker pull ghcr.io/sumitdalavi/secret-sprawl-remediation-bot:v0.2.0
docker run -d -p 8080:8080 --env-file .env ghcr.io/sumitdalavi/secret-sprawl-remediation-bot:v0.2.0
```
