"""Metadata about the account."""

import os
from typing import Optional

try:
    import boto3
except ImportError as err:
    raise ImportError(
        f"Error: boto3 not installed, install extra 'pip install boto3 to read AWS account attributes. \n{str(err)}"
    ) from err


def get_aws_account_id() -> str:
    """Get AWS account ID."""
    aws_profile: Optional[str] = os.getenv("AWS_PROFILE")

    if aws_profile:
        print(f"Using AWS_PROFILE value from environment: {aws_profile}.")
    else:
        print(
            "Warning: AWS_PROFILE environment variable not set. Setting --profile has no effect. AWS access keys or RBAC will be used instead."
        )

    session = boto3.Session(profile_name=aws_profile)
    return session.client("sts").get_caller_identity()["Account"]
