"""Boilerplate stack to make sure the CDK is set up correctly."""


import aws_cdk as cdk
from aws_cdk import Stack
from aws_cdk import aws_s3 as s3
from constructs import Construct

from cdk_clearml.clearml_backup_docker_image import ClearMLBackupServiceImage
from cdk_clearml.dns import map_subdomain_to_ec2_ip
from cdk_clearml.ec2_instance import ClearMLServerEC2Instance


class ClearMLStack(Stack):
    """Everything needed to run the ClearML Server on AWS."""

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        clearml_s3_backup_docker_image = ClearMLBackupServiceImage(self, "ClearMLS3BackupDockerImage")

        clearml_instance = ClearMLServerEC2Instance(
            self,
            "ClearMLServerEC2Instance",
            image_uri=clearml_s3_backup_docker_image.image_uri,
            ecr_repo_arn=clearml_s3_backup_docker_image.ecr_repo_arn,
        )
        clearml_s3_backup_docker_image.grant_pull(clearml_instance.ec2_instance.role)

        artifact_bucket = s3.Bucket(
            self,
            "clearml-artifact-storage",
            versioned=False,
            encryption=s3.BucketEncryption.S3_MANAGED,
            # Change to retain for production.
            removal_policy=cdk.RemovalPolicy.DESTROY,
        )
        artifact_bucket.grant_read_write(clearml_instance.ec2_instance.role)

        backups_bucket = s3.Bucket(
            self,
            "clearml-backups-storage",
            auto_delete_objects=True,
            versioned=False,
            encryption=s3.BucketEncryption.S3_MANAGED,
            removal_policy=cdk.RemovalPolicy.DESTROY,
        )

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
