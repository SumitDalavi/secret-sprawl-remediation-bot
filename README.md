# Secret Sprawl Remediation Bot

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

## Author

**Sumit Dalavi — Senior DevSecOps / Platform Engineer**
- [GitHub](https://github.com/your-username)
- [LinkedIn](https://linkedin.com/in/your-profile)


## CI & Reliability Updates (August 2026)

- **CI Pipeline Remediation:** Successfully resolved all CI/CD pipeline failures.
- **Specific Fix:** Added Flask to requirements for successful CI builds and service runtime.
- **Status:** 🟩 Passing
