"""Boilerplate stack to make sure the CDK is set up correctly."""


import aws_cdk as cdk
from aws_cdk import Stack
from aws_cdk import aws_s3 as s3
from constructs import Construct

from cdk_clearml.dns import map_subdomain_to_ec2_ip
from cdk_clearml.ec2_instance import ClearMLServerEC2Instance


class ClearMLStack(Stack):
    """Everything needed to run the ClearML Server on AWS."""

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        clearml_instance = ClearMLServerEC2Instance(self, "ClearMLServerEC2Instance")

        artifact_bucket = s3.Bucket(
            self,
            "clearml-artifact-storage",
            versioned=False,
            encryption=s3.BucketEncryption.S3_MANAGED,
            # Change to retain for production.
            removal_policy=cdk.RemovalPolicy.DESTROY,
        )

        artifact_bucket.grant_read_write(clearml_instance.ec2_instance.role)

        map_subdomain_to_ec2_ip(
            scope=self,
            ip_address=clearml_instance.ec2_instance.instance_public_ip,
            top_level_domain_name="mlops-club.org",
            subdomain="app.clearml",
        )
        map_subdomain_to_ec2_ip(
            scope=self,
            ip_address=clearml_instance.ec2_instance.instance_public_ip,
            top_level_domain_name="mlops-club.org",
            subdomain="files.clearml",
        )
        map_subdomain_to_ec2_ip(
            scope=self,
            ip_address=clearml_instance.ec2_instance.instance_public_ip,
            top_level_domain_name="mlops-club.org",
            subdomain="api.clearml",
        )
