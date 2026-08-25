import pytest
from src.bot import SecretScanner, RemediationBot

def test_secret_scanner():
    scanner = SecretScanner()
    diff = "+++ b/config.py\n+ api_key = 'abcdef1234567890abcdef1234567890'\n+ normal_var = 'test'"
    findings = scanner.scan_commit(diff)
    
    assert len(findings) == 1
    assert "abcdef" in findings[0]["line_content"]

def test_aws_key_scanner():
    scanner = SecretScanner()
    diff = "+++ b/main.tf\n+ access_key = 'AKIAIOSFODNN7EXAMPLE'"
    findings = scanner.scan_commit(diff)
    
    assert len(findings) == 1

def test_remediation_bot():
    bot = RemediationBot()
    payload = {
        "repository": "test-repo",
        "diff": "+ api_key = 'abcdef1234567890abcdef1234567890'"
    }
    result = bot.process_webhook(payload)
    
    assert result["secrets_found"] == 1
    assert len(result["tickets_created"]) == 1
    assert "SEC-" in result["tickets_created"][0]["ticket_id"]
