"""GitHub personal access token and OAuth token revocation."""
from __future__ import annotations
import os
from dataclasses import dataclass
from typing import Optional

try:
    import httpx
    _OK = True
except ImportError:
    _OK = False

GITHUB_API = "https://api.github.com"


@dataclass
class RevocationResult:
    provider: str
    secret_id: str
    success: bool
    message: str
    http_status: Optional[int] = None


def revoke_token(token: str, client_id: Optional[str] = None, client_secret: Optional[str] = None) -> RevocationResult:
    """
    Revoke a GitHub token.
    - PAT: DELETE /user/tokens (requires the token itself as auth)
    - OAuth token: DELETE /applications/{client_id}/token (requires app credentials)
    """
    masked = token[:8] + "..." + token[-4:] if len(token) > 12 else "****"

    if not _OK:
        return RevocationResult("github", masked, False, "httpx not installed")

    # OAuth app token revocation
    if client_id and client_secret:
        try:
            resp = httpx.delete(
                f"{GITHUB_API}/applications/{client_id}/token",
                auth=(client_id, client_secret),
                json={"access_token": token},
                timeout=10,
            )
            if resp.status_code in (204, 200):
                return RevocationResult("github", masked, True, "OAuth token revoked", resp.status_code)
            return RevocationResult("github", masked, False, f"Revocation failed: {resp.text}", resp.status_code)
        except Exception as e:
            return RevocationResult("github", masked, False, f"Request error: {e}")

    # Authenticated token deletion (PAT)
    try:
        resp = httpx.delete(
            f"{GITHUB_API}/user/tokens",
            headers={"Authorization": f"token {token}", "Accept": "application/vnd.github+json"},
            timeout=10,
        )
        if resp.status_code == 204:
            return RevocationResult("github", masked, True, "PAT revoked", 204)
        return RevocationResult("github", masked, False, f"Failed: {resp.status_code} {resp.text}", resp.status_code)
    except Exception as e:
        return RevocationResult("github", masked, False, f"Request error: {e}")
