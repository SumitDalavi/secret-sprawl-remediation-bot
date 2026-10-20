# Changelog — secret-sprawl-remediation-bot

## [0.2.0] - 2026-10-20
### Added
- **Progressive Credential Loading (PCL):** Dynamic auto-promotion between zero-dependency mock fallbacks and live production backends based on environment credentials.
- **Dual Distribution:** Universal OCI container publishing to GitHub Container Registry (`ghcr.io/sumitdalavi/secret-sprawl-remediation-bot`) and Helm OCI registries alongside GitHub Release tarballs.
- **Health Reporting:** Exposed `/health` or `/healthz` endpoint with PCL status detection (`mock` vs `live`).
- **Dynamic Reloading:** Support for atomic ConfigMap / secret reloads without requiring pod restarts.
- **Supply Chain Security:** Trivy vulnerability scan gates and SPDX JSON SBOM (`sbom.spdx.json`) generation for all releases.

## [0.1.0] - 2026-10-18
### Added
- Initial baseline service implementation, unit test suites, and CI workflows.

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
