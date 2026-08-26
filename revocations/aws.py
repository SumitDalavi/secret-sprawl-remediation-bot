"""AWS IAM access key deactivation and deletion."""
from __future__ import annotations
import os
from dataclasses import dataclass
from typing import Optional

from revocations.github import RevocationResult

try:
    import boto3
    _BOTO3 = True
except ImportError:
    _BOTO3 = False


def deactivate_access_key(access_key_id: str, username: Optional[str] = None) -> RevocationResult:
    """
    Deactivate an AWS IAM access key (non-destructive — key remains but is disabled).
    Safe first step; call delete_access_key after confirming no active usage.
    """
    masked = access_key_id[:8] + "..."

    if not _BOTO3:
        return RevocationResult("aws", masked, False, "boto3 not installed")

    try:
        iam = boto3.client(
            "iam",
            aws_access_key_id=os.getenv("REMEDIATION_AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("REMEDIATION_AWS_SECRET_ACCESS_KEY"),
        )
        kwargs = {"AccessKeyId": access_key_id, "Status": "Inactive"}
        if username:
            kwargs["UserName"] = username
        iam.update_access_key(**kwargs)
        return RevocationResult("aws", masked, True, f"Key {masked} deactivated (Inactive)")
    except Exception as e:
        return RevocationResult("aws", masked, False, f"boto3 error: {e}")


def delete_access_key(access_key_id: str, username: Optional[str] = None) -> RevocationResult:
    """Permanently delete an AWS IAM access key."""
    masked = access_key_id[:8] + "..."

    if not _BOTO3:
        return RevocationResult("aws", masked, False, "boto3 not installed")

    try:
        iam = boto3.client("iam",
            aws_access_key_id=os.getenv("REMEDIATION_AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("REMEDIATION_AWS_SECRET_ACCESS_KEY"),
        )
        kwargs = {"AccessKeyId": access_key_id}
        if username:
            kwargs["UserName"] = username
        iam.delete_access_key(**kwargs)
        return RevocationResult("aws", masked, True, f"Key {masked} permanently deleted")
    except Exception as e:
        return RevocationResult("aws", masked, False, f"boto3 error: {e}")
