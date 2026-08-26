"""GCP service account key deletion."""
from __future__ import annotations
import os
from revocations.github import RevocationResult

try:
    from google.oauth2 import service_account
    from googleapiclient import discovery
    _GCP = True
except ImportError:
    _GCP = False


def delete_service_account_key(project_id: str, sa_email: str, key_id: str) -> RevocationResult:
    """
    Delete a GCP service account key via the IAM API.
    Requires: roles/iam.serviceAccountKeyAdmin on the project.
    """
    resource_name = f"projects/{project_id}/serviceAccounts/{sa_email}/keys/{key_id}"
    masked_key = key_id[:12] + "..."

    if not _GCP:
        return RevocationResult("gcp", masked_key, False, "google-api-python-client not installed")

    try:
        # Use Application Default Credentials
        service = discovery.build("iam", "v1")
        service.projects().serviceAccounts().keys().delete(name=resource_name).execute()
        return RevocationResult("gcp", masked_key, True, f"Key {masked_key} deleted from {sa_email}")
    except Exception as e:
        return RevocationResult("gcp", masked_key, False, f"GCP API error: {e}")
