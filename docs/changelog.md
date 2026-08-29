# Changelog — secret-sprawl-remediation-bot

## [2026-08-29] — Phase 0 fixes (Portfolio Action Plan)
### Fixed
- `src/bot.py`: Added `FALLBACK_PATTERNS` list (4 compiled regex patterns) and `GitleaksScanner._scan_with_regex()`. When `gitleaks` binary is not in PATH (`FileNotFoundError`), scanner falls back to in-process regex detection on diff `+` lines. Fixes `test_src_bot` assertion (`secrets_found == 2`) which previously got 0 when gitleaks wasn't installed.
- `src/bot.py`: Restructured imports — moved `tempfile`, `subprocess`, `json` imports to top-level (were previously in the middle of the class, causing lint warnings).
- `src/bot.py`: `scan_commit()` now has explicit `gitleaks_ok` flag; fallback only activates if gitleaks subprocess fails or is not found.
### Added
- `docs/architecture.md`: Expanded from 22-line placeholder to full Mermaid flowchart with all 10 components, dependency honesty table, fallback pattern table, port assignments.
- `docs/runbook.md`: New — Windows-aware venv setup, quick start, exact test output, batch mode, webhook curl example, env vars, failure modes.
- `docs/decisions.md`: New — four ADRs covering dual-mode scanner, two entry points, Redis graceful degradation, provider-per-module pattern.
- `docs/changelog.md`: New (this file).

## [Pre-2026-08-29] — Initial implementation
### Added
- FastAPI webhook server (`src/bot.py`) — `POST /webhook` with gitleaks scanning
- Revocation modules for GitHub, AWS, GCP (`revocations/`)
- Jira ticketing (`jira/ticket.py`), Slack notifications (`notifications/slack.py`)
- Root CLI bot (`bot.py`) — batch mode from Gitleaks JSON report
- Mock Flask API (`mock_api/server.py`) — IdP simulation
- pytest test suite (`tests/test_all.py`) — 10 tests with mocked external dependencies
- Docker support (`Dockerfile`, `Dockerfile.api`, `Dockerfile.bot`)
- GitHub Actions CI pipeline
