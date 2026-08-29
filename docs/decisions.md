# Architecture Decision Records — secret-sprawl-remediation-bot
> Last updated: 2026-08-29

---

## ADR-001: Dual-Mode Scanner — gitleaks Primary, Regex Fallback

**Date:** 2026-08-29  
**Status:** Accepted

**Context:**  
`GitleaksScanner.scan_commit()` originally invoked the `gitleaks` binary via `subprocess.run`. In test environments without `gitleaks` installed, the scanner silently returned 0 findings. The test `test_src_bot` expected `secrets_found == 2` but got 0, causing a test failure.

**Decision:**  
Added `FALLBACK_PATTERNS` (a list of compiled regex patterns) and `_scan_with_regex()`. The scan flow is:
1. Try `gitleaks detect` subprocess
2. On `FileNotFoundError` (binary not in PATH) or any subprocess error, call `_scan_with_regex()` instead
3. Regex scan runs line-by-line on `+` diff lines only

**Consequences:**  
- ✅ Tests pass without installing `gitleaks`  
- ✅ Production scanner still prefers `gitleaks` (more comprehensive rule set)  
- ⚠️ Regex patterns are curated for common types — novel secret formats require gitleaks  
- ⚠️ Regex may have false positives for long random strings matching generic patterns

---

## ADR-002: FastAPI Webhook + Root CLI Bot — Two Entry Points

**Date:** Pre-2026-08-29  
**Status:** Accepted

**Context:**  
Two use cases: (1) real-time webhook integration (GitHub Actions/webhook), (2) batch processing of an existing Gitleaks report file.

**Decision:**  
Two separate entry points:
- `src/bot.py` (FastAPI app) — `POST /webhook` for real-time diff scanning
- `bot.py` (root) — CLI script that reads a JSON report and POSTs each finding to the mock API

**Consequences:**  
- ✅ Demonstrates both real-time and batch remediation patterns  
- ⚠️ The root `bot.py` is a demo/CLI tool; it depends on `mock_api/server.py` being running

---

## ADR-003: Redis for Dedup with Graceful Degradation

**Date:** Pre-2026-08-29  
**Status:** Accepted

**Context:**  
The same secret might appear in multiple commits (e.g., a leaked key not yet rotated). Without dedup, every push would trigger repeated revocation attempts and Jira tickets.

**Decision:**  
Redis is used as a dedup cache: `secret:{hash}` key with 30-day TTL. If Redis is unavailable (connection error), the dedup check is skipped with a `try/except` — the bot processes the secret anyway.

**Consequences:**  
- ✅ Bot is resilient — works even without Redis  
- ✅ 30-day TTL prevents stale dedup entries  
- ⚠️ Without Redis, the same secret triggers repeated tickets if pushed again within 30 days

---

## ADR-004: Separate Revocation Modules per Provider

**Date:** Pre-2026-08-29  
**Status:** Accepted

**Context:**  
AWS, GitHub, and GCP each have completely different APIs for revoking credentials. Mixing them in one file would make it hard to add new providers.

**Decision:**  
Each provider has its own module: `revocations/github.py`, `revocations/aws.py`, `revocations/gcp.py`. Each exports a `RevocationResult` dataclass with `(provider, secret_id, success, message)`.

**Consequences:**  
- ✅ Easy to add new providers (Azure, Vault, etc.) without touching orchestration logic  
- ✅ Each module independently mockable in tests
