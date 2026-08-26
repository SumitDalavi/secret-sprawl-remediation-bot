"""Slack notification sender for secret remediation events."""
from __future__ import annotations
import os
from typing import List
from revocations.github import RevocationResult

try:
    import httpx
    _OK = True
except ImportError:
    _OK = False

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")


def send_remediation_alert(findings: List[dict], results: List[RevocationResult]) -> bool:
    """Send a Slack notification summarising detected secrets and remediation actions."""
    if not SLACK_WEBHOOK_URL or not _OK:
        print("[slack] No webhook URL or httpx not installed — skipping notification")
        return False

    succeeded = sum(1 for r in results if r.success)
    failed = sum(1 for r in results if not r.success)
    emoji = ":white_check_mark:" if failed == 0 else ":warning:"

    fields = []
    for r in results:
        fields.append({
            "type": "mrkdwn",
            "text": f"*{r.provider.upper()}*: {'✅' if r.success else '❌'} {r.message}"
        })

    payload = {
        "blocks": [
            {"type": "header", "text": {"type": "plain_text", "text": f"{emoji} Secret Sprawl Remediation Alert"}},
            {"type": "section", "text": {
                "type": "mrkdwn",
                "text": f"*{len(findings)} secret(s) detected* — {succeeded} revoked, {failed} failed"
            }},
            {"type": "divider"},
            {"type": "section", "fields": fields[:10]},  # Slack limit
        ]
    }
    try:
        resp = httpx.post(SLACK_WEBHOOK_URL, json=payload, timeout=8)
        return resp.status_code == 200
    except Exception as e:
        print(f"[slack] Error: {e}")
        return False
