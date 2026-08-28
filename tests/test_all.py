import pytest
import sys
from unittest.mock import patch, MagicMock

# Mock out external libraries early
sys.modules['boto3'] = MagicMock()
sys.modules['google'] = MagicMock()
sys.modules['google.oauth2'] = MagicMock()
sys.modules['google.oauth2.service_account'] = MagicMock()
sys.modules['googleapiclient'] = MagicMock()
sys.modules['googleapiclient.discovery'] = MagicMock()

import httpx
import boto3
from googleapiclient import discovery

import bot as root_bot
from src.bot import GitleaksScanner
from jira.ticket import create_remediation_ticket
from notifications.slack import send_remediation_alert
from revocations.github import revoke_token, RevocationResult
from revocations.aws import deactivate_access_key, delete_access_key
from revocations.gcp import delete_service_account_key
from mock_api.server import app
import json

# --- root/bot.py ---
@patch('bot.requests.post')
def test_root_bot(mock_post, tmp_path):
    report_file = tmp_path / "report.json"
    report_file.write_text(json.dumps([{
        "Secret": "test_secret",
        "RuleID": "test_rule",
        "Description": "test_desc"
    }]))
    
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {"message": "ok"}
    
    with patch('sys.argv', ['bot.py', str(report_file)]):
        root_bot.main()

@patch('bot.requests.post')
def test_root_bot_error(mock_post, tmp_path):
    report_file = tmp_path / "report.json"
    report_file.write_text(json.dumps([{
        "Secret": "test_secret",
        "RuleID": "test_rule",
        "Description": "test_desc"
    }]))
    
    mock_post.return_value.status_code = 404
    with patch('sys.argv', ['bot.py', str(report_file)]):
        root_bot.main()
    import requests
    mock_post.side_effect = requests.exceptions.RequestException("network")
    with patch('sys.argv', ['bot.py', str(report_file)]):
        root_bot.main()

def test_root_bot_load_error(tmp_path):
    with patch('sys.argv', ['bot.py', str(tmp_path / 'invalid')]):
        with pytest.raises(SystemExit):
            root_bot.main()


# --- src/bot.py ---
from fastapi.testclient import TestClient
from src.bot import app

client = TestClient(app)

def test_src_bot():
    payload = {
        "repository": "my-app",
        "diff": "+++ b/config.py\n+ AWS_KEY = 'AKIAIOSFODNN7EXAMPLE'\n+ key = 'api_key=123456789012345678901234567890123'"
    }
    with patch('src.bot.create_remediation_ticket') as mock_ticket, \
         patch('src.bot.send_remediation_alert') as mock_slack, \
         patch('src.bot.revoke_token'), \
         patch('src.bot.deactivate_access_key'):
        mock_ticket.return_value = "SEC-123"
        res = client.post("/webhook", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data['secrets_found'] == 2

def test_src_bot_no_secrets():
    payload = {
        "repository": "my-app",
        "diff": "+++ b/config.py\n+ nothing interesting"
    }
    res = client.post("/webhook", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data['secrets_found'] == 0


# --- jira/ticket.py ---
def test_jira_ticket():
    res = RevocationResult(provider='github', secret_id='123', success=True, message='ok')
    with patch('jira.ticket.httpx.post') as mock_post:
        mock_post.return_value.status_code = 201
        mock_post.return_value.json.return_value = {'key': 'SEC-123'}
        with patch('jira.ticket.JIRA_URL', 'url'), patch('jira.ticket.JIRA_USER', 'u'), patch('jira.ticket.JIRA_TOKEN', 't'), patch('jira.ticket._OK', True):
            key = create_remediation_ticket([{'line_number':1, 'line_content':'test'}], [res])
            assert key == 'SEC-123'
            
        # Test failed create
        mock_post.return_value.status_code = 500
        with patch('jira.ticket.JIRA_URL', 'url'), patch('jira.ticket.JIRA_USER', 'u'), patch('jira.ticket.JIRA_TOKEN', 't'), patch('jira.ticket._OK', True):
            assert create_remediation_ticket([{}], [res]) is None
            
        # Test missing creds
        assert create_remediation_ticket([{}], [res]) is None
        
        # Test exception
        mock_post.side_effect = Exception("error")
        with patch('jira.ticket.JIRA_URL', 'url'), patch('jira.ticket.JIRA_USER', 'u'), patch('jira.ticket.JIRA_TOKEN', 't'), patch('jira.ticket._OK', True):
            assert create_remediation_ticket([{}], [res]) is None


# --- notifications/slack.py ---
def test_slack_alert():
    with patch('notifications.slack.httpx.post') as mock_post:
        mock_post.return_value.status_code = 200
        with patch('notifications.slack.SLACK_WEBHOOK_URL', 'url'), patch('notifications.slack._OK', True):
            send_remediation_alert([{'line_number':1, 'line_content':'test'}], [RevocationResult(provider='github', secret_id='123', success=True, message='ok')])
            
        # Error
        mock_post.side_effect = Exception("error")
        with patch('notifications.slack.SLACK_WEBHOOK_URL', 'url'), patch('notifications.slack._OK', True):
            send_remediation_alert([{}], [])
            
        # No URL
        with patch('notifications.slack.SLACK_WEBHOOK_URL', ''), patch('notifications.slack._OK', True):
            send_remediation_alert([{}], [])


# --- revocations ---
def test_github_revoke():
    with patch('revocations.github.httpx.delete') as mock_delete:
        mock_delete.return_value.status_code = 204
        with patch('revocations.github._OK', True):
            res = revoke_token('ghp_token')
            assert res.success
            
        mock_delete.return_value.status_code = 404
        with patch('revocations.github._OK', True):
            res = revoke_token('ghp_token')
            assert not res.success
            
        mock_delete.side_effect = Exception("error")
        with patch('revocations.github._OK', True):
            res = revoke_token('ghp_token')
            assert not res.success
            
        # OAuth app token revocation
        mock_delete.side_effect = None
        mock_delete.return_value.status_code = 204
        with patch('revocations.github._OK', True):
            res = revoke_token('ghp_token', 'client_id', 'client_secret')
            assert res.success

        mock_delete.return_value.status_code = 404
        with patch('revocations.github._OK', True):
            res = revoke_token('ghp_token', 'client_id', 'client_secret')
            assert not res.success
            
        mock_delete.side_effect = Exception("error")
        with patch('revocations.github._OK', True):
            res = revoke_token('ghp_token', 'client_id', 'client_secret')
            assert not res.success
            
        with patch('revocations.github._OK', False):
            res = revoke_token('ghp_token')
            assert not res.success

def test_aws_revoke():
    with patch('revocations.aws.boto3') as mock_boto:
        mock_client = MagicMock()
        mock_boto.client.return_value = mock_client
        
        with patch('revocations.aws._BOTO3', True):
            res = deactivate_access_key('AKIA123')
            assert res.success
            
            res = delete_access_key('AKIA123')
            assert res.success

            # username provided
            res = deactivate_access_key('AKIA123', 'user')
            assert res.success
            res = delete_access_key('AKIA123', 'user')
            assert res.success

            mock_client.update_access_key.side_effect = Exception("error")
            res = deactivate_access_key('AKIA123')
            assert not res.success
            
            mock_client.delete_access_key.side_effect = Exception("error")
            res = delete_access_key('AKIA123')
            assert not res.success
            
        with patch('revocations.aws._BOTO3', False):
            res = deactivate_access_key('AKIA123')
            assert not res.success
            res = delete_access_key('AKIA123')
            assert not res.success

def test_gcp_revoke():
    with patch('revocations.gcp.discovery.build') as mock_build:
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        
        with patch('revocations.gcp._GCP', True):
            res = delete_service_account_key('project', 'sa', 'key')
            assert res.success
            
            mock_service.projects().serviceAccounts().keys().delete().execute.side_effect = Exception("error")
            res = delete_service_account_key('project', 'sa', 'key')
            assert not res.success
            
        with patch('revocations.gcp._GCP', False):
            res = delete_service_account_key('project', 'sa', 'key')
            assert not res.success



