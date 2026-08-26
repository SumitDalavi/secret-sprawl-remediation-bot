"""Tests for secret revocation modules."""
import pytest
from unittest.mock import patch, MagicMock
from revocations.github import revoke_token, RevocationResult


def test_revoke_token_no_httpx(monkeypatch):
    monkeypatch.setattr("revocations.github._OK", False)
    result = revoke_token("ghp_test1234567890abcdef")
    assert not result.success
    assert "not installed" in result.message


def test_revoke_token_pat_success():
    with patch("revocations.github._OK", True), patch("revocations.github.httpx") as mock_httpx:
        mock_resp = MagicMock()
        mock_resp.status_code = 204
        mock_httpx.delete.return_value = mock_resp
        result = revoke_token("ghp_test1234567890abcdef")
    assert result.success
    assert result.http_status == 204


def test_revoke_token_oauth_success():
    with patch("revocations.github._OK", True), patch("revocations.github.httpx") as mock_httpx:
        mock_resp = MagicMock()
        mock_resp.status_code = 204
        mock_httpx.delete.return_value = mock_resp
        result = revoke_token("token123", client_id="client", client_secret="secret")
    assert result.success


def test_revoke_token_failure():
    with patch("revocations.github._OK", True), patch("revocations.github.httpx") as mock_httpx:
        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_resp.text = "Unauthorized"
        mock_httpx.delete.return_value = mock_resp
        result = revoke_token("bad_token_1234567890")
    assert not result.success
    assert "401" in result.message


def test_revocation_result_dataclass():
    r = RevocationResult("aws", "AKIA****", True, "Key deactivated", 200)
    assert r.provider == "aws"
    assert r.success is True
