"""Jira ticket creation for secret remediation incidents."""
from __future__ import annotations
import os
from typing import List, Optional
from revocations.github import RevocationResult

try:
    import httpx
    _OK = True
except ImportError:
    _OK = False

JIRA_URL = os.getenv("JIRA_URL", "")
JIRA_USER = os.getenv("JIRA_USER", "")
JIRA_TOKEN = os.getenv("JIRA_TOKEN", "")
JIRA_PROJECT = os.getenv("JIRA_PROJECT", "SEC")


def create_remediation_ticket(
    findings: List[dict],
    results: List[RevocationResult],
    priority: str = "High",
) -> Optional[str]:
    """Create a Jira security incident ticket. Returns the ticket key (e.g. SEC-123) or None."""
    if not (JIRA_URL and JIRA_USER and JIRA_TOKEN) or not _OK:
        print("[jira] Missing credentials or httpx — skipping ticket creation")
        return None

    failed_revocations = [r for r in results if not r.success]
    summary = f"Secret Sprawl: {len(findings)} secret(s) detected — {len(failed_revocations)} revocation(s) failed"

    finding_lines = "\n".join(
        f"- Line {f.get('line_number', '?')}: {f.get('line_content', '')[:80]}" for f in findings[:10]
    )
    revocation_lines = "\n".join(
        f"- [{r.provider.upper()}] {'SUCCESS' if r.success else 'FAILED'}: {r.message}" for r in results
    )

    payload = {
        "fields": {
            "project": {"key": JIRA_PROJECT},
            "summary": summary,
            "description": {
                "type": "doc", "version": 1,
                "content": [{"type": "paragraph", "content": [{"type": "text", "text":
                    f"Findings:\n{finding_lines}\n\nRemediation Actions:\n{revocation_lines}"
                }]}],
            },
            "issuetype": {"name": "Bug"},
            "priority": {"name": priority},
            "labels": ["security", "secret-sprawl", "automated"],
        }
    }

    try:
        resp = httpx.post(
            f"{JIRA_URL}/rest/api/3/issue",
            auth=(JIRA_USER, JIRA_TOKEN),
            json=payload,
            timeout=10,
        )
        if resp.status_code == 201:
            key = resp.json().get("key")
            print(f"[jira] Ticket created: {JIRA_URL}/browse/{key}")
            return key
        print(f"[jira] Failed: {resp.status_code} {resp.text}")
        return None
    except Exception as e:
        print(f"[jira] Error: {e}")
        return None
