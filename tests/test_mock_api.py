import pytest
from mock_api.server import app, VALID_TOKENS

@pytest.fixture
def client():
    with app.test_client() as client:
        yield client

def test_revoke_success(client):
    secret = "AKIAIOSFODNN7EXAMPLE"
    VALID_TOKENS[secret]["status"] = "active" # Reset
    res = client.post("/api/v1/revoke", json={"secret": secret, "rule_id": "aws-key"})
    assert res.status_code == 200
    assert res.json["status"] == "success"

def test_revoke_not_found(client):
    res = client.post("/api/v1/revoke", json={"secret": "unknown", "rule_id": "aws-key"})
    assert res.status_code == 404
