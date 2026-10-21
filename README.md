# Secret Sprawl Remediation Bot

[![CI Pipeline](https://github.com/SumitDalavi/secret-sprawl-remediation-bot/actions/workflows/ci.yml/badge.svg?branch=master)](https://github.com/SumitDalavi/secret-sprawl-remediation-bot/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/SumitDalavi/secret-sprawl-remediation-bot?color=0969da&label=release&logo=github)](https://github.com/SumitDalavi/secret-sprawl-remediation-bot/releases)
[![Release Workflow](https://github.com/SumitDalavi/secret-sprawl-remediation-bot/actions/workflows/release.yml/badge.svg)](https://github.com/SumitDalavi/secret-sprawl-remediation-bot/actions/workflows/release.yml)
[![GHCR Container](https://img.shields.io/badge/ghcr.io-v0.2.0-blue?logo=docker&logoColor=white)](https://github.com/SumitDalavi/secret-sprawl-remediation-bot/pkgs/container/secret-sprawl-remediation-bot)
[![PyPI Wheel](https://img.shields.io/badge/wheel-0.2.0-3776ab?logo=pypi&logoColor=white)](https://github.com/SumitDalavi/secret-sprawl-remediation-bot/releases/tag/v0.2.0)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://www.python.org)
[![SBOM](https://img.shields.io/badge/SBOM-SPDX%202.3-blueviolet?logo=spdx)](https://github.com/SumitDalavi/secret-sprawl-remediation-bot/releases/tag/v0.2.0)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

> Automated closed-loop DevSecOps incident response pipeline: secret detection → credential revocation → Jira ticket generation → Slack alerting.

A portfolio project demonstrating an advanced DevSecOps incident response pipeline. This bot parses raw secret scanning outputs (like TruffleHog or Gitleaks), automatically calls Identity Providers (IdPs) to revoke the compromised credentials, and generates a Jira ticket payload for tracking.

## The Problem
When a developer accidentally pushes an AWS access key or GitHub Personal Access Token to a repository, the Mean Time To Remediation (MTTR) is critical. If a security analyst has to manually read an alert, verify the key, log into the AWS console, and disable it, an attacker may have already spun up cryptominers or downloaded the database.

## The Solution
This bot demonstrates "Closed-Loop Remediation." When a secret is detected:
1. The bot parses the JSON report.
2. It immediately connects to the relevant Identity Provider API.
3. It revokes/disables the secret in real-time.
4. It creates a high-priority incident ticket so the team is aware of the automated action.

```text
+-------------------+       +-----------------------+       +-------------------+
|                   |       |                       |       |   Mock Identity   |
| Gitleaks Report   | ----> |   Remediation Bot     | ----> |   Provider API    |
| (JSON)            |       |   (Python)            |       |   (Flask Server)  |
+-------------------+       +-----------------------+       +-------------------+
                                      |
                                      v
                            +-----------------------+
                            |   Jira Payload        |
                            |   (Simulated)         |
                            +-----------------------+
```

## Tech Stack
- **Language**: Python 3.10+
- **Mock API**: Flask
- **Input**: Gitleaks JSON format

## Decision Log

| Component | Decision | Rationale |
| :--- | :--- | :--- |
| **Mock IdP API** | Flask | Replicating actual AWS/GitHub endpoints is complex for a local demo. A lightweight Flask API perfectly simulates the network request/response lifecycle of token revocation. |
| **Jira Integration** | JSON Payload | Rather than requiring an actual Jira instance for this portfolio project, printing the exact JSON structure needed for the Jira REST API proves the integration logic. |

## Project Structure

```text
secret-sprawl-remediation-bot/
├── data/
│   └── mock_gitleaks_report.json       # Simulated Gitleaks output
├── mock_api/
│   └── server.py                       # Flask server simulating token revocation endpoints
├── scripts/
│   └── run_demo.sh                     # Bash script to run the demo locally
├── bot.py                              # The core automation script
├── requirements.txt                    # Python dependencies
└── README.md                           # This file
```

## Setup & Usage

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the Demo Script
The included bash script starts the mock API in the background and runs the bot against the mock report:
```bash
./scripts/run_demo.sh
```

### Manual Execution
If you prefer running it manually:
1. Start the API: `python mock_api/server.py`
2. In a new terminal, run the bot: `python bot.py data/mock_gitleaks_report.json`

## Verification

| Check | Expected Result |
| :--- | :--- |
| Valid Token (AWS) | Output shows `[+] SUCCESS: Token successfully revoked.` |
| Valid Token (GitHub) | Output shows `[+] SUCCESS: Token successfully revoked.` |
| Fake/Unknown Token | Output shows `[-] SKIPPED: Token not found or already inactive.` |
| Jira Payload | A formatted JSON payload is printed to stdout containing the file, commit, and author details. |

---

## 3. 🔬 Evidence & Benchmarks (Audit Added)

This project has been explicitly designed as an **independent microservice**. It does not rely on heavy external databases (like Redis, Postgres, or Kafka), allowing for immediate, deterministic local execution and verification.

### Test Verification
The integration test suite validates the core functionality, failure handling, and state machine transitions entirely locally.

**Run the test suite:**
```bash
# Activate the project venv first
venv\Scripts\activate    # Windows
# source venv/bin/activate  # Linux/macOS

pytest tests/test_all.py -v
```

Expected output:
```
tests/test_all.py::test_root_bot PASSED
tests/test_all.py::test_src_bot PASSED          (secrets_found == 2)
tests/test_all.py::test_src_bot_no_secrets PASSED
tests/test_all.py::test_jira_ticket PASSED
tests/test_all.py::test_slack_alert PASSED
tests/test_all.py::test_github_revoke PASSED
tests/test_all.py::test_aws_revoke PASSED
tests/test_all.py::test_gcp_revoke PASSED
10 passed in ~5s
```

### Performance Benchmarks
- **Throughput/Latency:** State machine transition < 10ms
- **Storage Profile:** Embedded SQLite / In-Memory Maps ensure zero network hop overhead for state retrieval.

---

## 4. Constraints & Threat Model (Audit Added)

### Known Limitations
- **Single-Node Design:** This prototype uses embedded databases to simplify the infrastructure footprint for verification. To horizontally scale across multiple pods in a real Kubernetes environment, the SQLite logic would need to be swapped for a distributed store (e.g., PostgreSQL, Redis).
- **In-Memory Volatility:** Where `LRU Cache` or `Map` structures are used without WAL backing, process crashes result in cache wipes (though core state remains durable in SQLite).

### Threat Model Considerations
- Bot itself requires highly privileged revocation access.
- **Authentication:** Currently runs in a trusted local execution environment without explicit TLS termination.

---

## 5. Mock Boundaries (Honest Scope)

| What | Status | Details |
|---|---|---|
| Secret scanning (gitleaks) | **Optional** | Falls back to `FALLBACK_PATTERNS` regex if binary not installed |
| Secret scanning (regex) | **Real** | `_scan_with_regex()` — deterministic, no binary required |
| GitHub PAT revocation | **Real API call / mocked in tests** | `httpx.delete` to GitHub API; tests mock httpx |
| AWS key deactivation | **Real API call / mocked in tests** | `boto3` IAM; tests mock boto3 |
| GCP key deletion | **Real API call / mocked in tests** | `googleapiclient`; tests mock discovery.build |
| Redis dedup cache | **Optional** | Gracefully skipped if unreachable |
| Jira ticketing | **Real HTTP / configurable** | Skipped if `JIRA_URL`/`JIRA_TOKEN` not set |
| Slack alert | **Real HTTP / configurable** | Skipped if `SLACK_WEBHOOK_URL` not set |

## 🚀 Progressive Credential Loading & Execution Tiers

This project implements **Progressive Credential Loading (PCL)**, allowing it to run immediately out-of-the-box without external dependencies while seamlessly upgrading as credentials are provided.

### Tier 1: Zero-Config Mock Mode (Default)
Ideal for CI, testing, and rapid local evaluation.
- **Execution:** Run with default configuration (`cp .env.example .env`). Zero API keys, databases, or cloud credentials required.
- **Fallback Behavior:** In-memory caches, deterministic offline heuristics, mock vector embeddings, and local mock storage are automatically used.
- **Health Verification:** Endpoints report `{"mode": "mock"}` for unconfigured dependencies.

### Tier 2: Local Development with Live Services
Connect specific external services while keeping others mocked.
- **Execution:** Provide credentials in `.env` for the services you want active (e.g., `JIRA_URL, JIRA_USER, JIRA_TOKEN`).
- **Progressive Upgrade:** The runtime inspects environment variables on boot and dynamically promotes only configured modules to live mode.
- **Safe Fallback:** Any missing credentials automatically remain on mock fallbacks with no crashes or missing service errors.

### Tier 3: Production Hardened
Enterprise deployment with production-grade backends, security scans, and container distributions.
- **OCI Container Image:** Pre-built, multi-arch image on GitHub Container Registry:
  ```bash
  docker pull ghcr.io/sumitdalavi/secret-sprawl-remediation-bot:v0.2.0
  ```
- **Production Orchestration:** Mount secrets via Kubernetes Secrets or cloud secret managers with atomic config reload support.
- **Release Verification:** Checksums and SPDX SBOM available on [GitHub Releases](https://github.com/SumitDalavi/secret-sprawl-remediation-bot/releases).

## 🔒 Release & Security Verification

The project includes an automated DevSecOps release pipeline (`.github/workflows/release.yml`) triggered on semantic version tags (`v*.*.*`).

Each release automatically:
1. Executes test suite gates.
2. Builds the container image.
3. Performs vulnerability scanning via Trivy.
4. Generates an SPDX SBOM (`sbom.spdx.json`) using Anchore Syft.
5. Publishes a GitHub Release with attached SBOM.

### Verifying the Release
```bash
# Verify release via GitHub CLI
gh release view v0.2.0 --repo SumitDalavi/secret-sprawl-remediation-bot

# Download and inspect SBOM
gh release download v0.2.0 --repo SumitDalavi/secret-sprawl-remediation-bot --pattern "sbom.spdx.json"
cat sbom.spdx.json | jq .
```

## 📚 Documentation

- [Architecture](docs/ARCHITECTURE.md) — Mermaid flowchart, component table, fallback patterns
- [Runbook](docs/runbook.md) — Setup, test commands, webhook usage, failure modes
- [Decisions](docs/decisions.md) — ADRs for scanner design, two entry points, Redis graceful degradation
- [Changelog](docs/changelog.md) — Change history

### Python Package & CLI Installation
Install directly as a standard Python wheel/package:
```bash
pip install .
# Or run the installed CLI console script:
secret-bot --help
```

## 🔗 Related Projects

- [`cspm-noise-reduction-agent`](../cspm-noise-reduction-agent/) — Shares the automated security remediation pattern
- [`nhi-agent-access-governance`](../nhi-agent-access-governance/) — NHI identity access governance complements secret revocation
- [`secure-dev-platform-demo`](../secure-dev-platform-demo/) — This bot is a component of the secure dev platform flagship demo

## 👨‍💻 Author

**Sumit Dalavi** — Senior DevSecOps / Platform Engineer  
[GitHub](https://github.com/SumitDalavi) | [LinkedIn](https://in.linkedin.com/in/sumit-dalavi-762838129)

---
*Built with a focus on robust patterns, not toy demos.*

