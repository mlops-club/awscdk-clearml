"""AWS CDK construct that builds the docker image for the Minecraft server backup service."""

from pathlib import Path

import cdk_ecr_deployment as ecr_deployment
from aws_cdk import aws_ecr as ecr
from aws_cdk import aws_ecr_assets as ecr_assets
from aws_cdk import aws_iam as iam
from constructs import Construct

THIS_DIR = Path(__file__).parent
CLEARML_PLATFORM_BACKUP_SERVICE__DIR = THIS_DIR / "./resources/clearml-s3-backup-service"

class ClearMLBackupServiceImage(Construct):
    def __init__(self, scope: "Construct", id: str, ensure_unique_ids: bool = False) -> None:
        """Build the docker image for the ClearML server backup service."""
        super().__init__(scope, id)

        self.namer = lambda name: f"{id}-{name}" if ensure_unique_ids else name

        # build the backup-service docker image
        clear_ml_backup_service_image = ecr_assets.DockerImageAsset(
            scope=scope,
            id=self.namer("ClearMLBackupServiceImage"),
            directory=str(CLEARML_PLATFORM_BACKUP_SERVICE__DIR),
            platform=ecr_assets.Platform.LINUX_AMD64,
        )

        # create an ECR repo to upload the image to
        self.ecr_repo_construct_id = 'ClearMLBackupServiceEcrRepo'
        self._ecr_repo = ecr.Repository(
            scope=scope,
            id=self.namer(self.ecr_repo_construct_id),
        )

        # push the image to the ECR repo
        ecr_deployment.ECRDeployment(
            scope=scope,
            id=self.namer("ClearMLBackupServiceEcrDeployment"),
            src=ecr_deployment.DockerImageName(clear_ml_backup_service_image.image_uri),
            dest=ecr_deployment.DockerImageName(self._ecr_repo.repository_uri),
        )

        self.image_uri = self._ecr_repo.repository_uri
        """Use this in 'docker pull <image_uri>' to pull the image from ECR."""

        self.ecr_repo_arn = self._ecr_repo.repository_arn
        """Use this to grant access to the ECR repo to other roles."""


    def grant_pull(self, role: iam.Role) -> None:
        ecr_repo = ecr.Repository.from_repository_arn(
            scope=role, 
            id=self.ecr_repo_construct_id, 
            repository_arn=self.ecr_repo_arn,
        )
        ecr_repo.grant_pull(role)