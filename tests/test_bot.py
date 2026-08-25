from bot import generate_jira_payload, load_report

def test_generate_jira_payload():
    finding = {
        "File": "config.yml",
        "Commit": "abc1234",
        "Author": "Dev",
        "Email": "dev@example.com",
        "RuleID": "aws-key",
        "Description": "AWS Access Key",
        "Secret": "dummy"
    }
    status = {"status": "success", "message": "Revoked"}
    
    payload = generate_jira_payload(finding, status)
    
    assert payload["fields"]["project"]["key"] == "SECINC"
    assert "abc1234" in payload["fields"]["description"]
    assert "Revoked" in payload["fields"]["description"]
