import json
import argparse
import requests
import sys

API_URL = "http://localhost:5000/api/v1/revoke"

def load_report(filepath):
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading report: {e}")
        sys.exit(1)

def revoke_secret(secret, rule_id):
    try:
        response = requests.post(API_URL, json={
            "secret": secret,
            "rule_id": rule_id
        }, timeout=5)
        return response.json(), response.status_code
    except requests.exceptions.RequestException as e:
        print(f"Failed to connect to Identity Provider API: {e}")
        return None, 500

def generate_jira_payload(finding, revocation_status):
    # Simulated Jira API payload for creating an incident ticket
    description = f"""
    *Secret Leaked in Git History!*
    File: {finding.get('File')}
    Commit: {finding.get('Commit')}
    Author: {finding.get('Author')} ({finding.get('Email')})
    Rule: {finding.get('RuleID')}
    
    *Automated Remediation Status:* {revocation_status.get('status')}
    *Details:* {revocation_status.get('message')}
    """
    
    payload = {
        "fields": {
            "project": {"key": "SECINC"},
            "summary": f"[Urgent] Leaked {finding.get('Description')} in {finding.get('File')}",
            "description": description,
            "issuetype": {"name": "Incident"},
            "priority": {"name": "Highest"}
        }
    }
    return payload

def main():
    parser = argparse.ArgumentParser(description="Secret Sprawl Remediation Bot")
    parser.add_argument("report", help="Path to the Gitleaks JSON report")
    args = parser.parse_args()

    findings = load_report(args.report)
    print(f"Loaded {len(findings)} findings from {args.report}.\n")

    for finding in findings:
        secret = finding.get("Secret")
        rule_id = finding.get("RuleID")
        desc = finding.get("Description")
        
        print(f"[*] Processing finding: {desc} (Rule: {rule_id})")
        print(f"    Attempting automated revocation via Identity Provider...")
        
        result, status = revoke_secret(secret, rule_id)
        
        if status == 200:
            print(f"    [+] SUCCESS: {result.get('message')}")
        elif status == 404:
            print(f"    [-] SKIPPED: Token not found or already inactive.")
        else:
            print(f"    [!] ERROR: Failed to revoke token.")

        # Generate Jira Ticket payload
        jira_payload = generate_jira_payload(finding, result if result else {"status": "error", "message": "API Failure"})
        print(f"    [>] Generated Jira Incident Payload (Simulated):")
        print(json.dumps(jira_payload, indent=2))
        print("-" * 50)

if __name__ == "__main__":
    main()
