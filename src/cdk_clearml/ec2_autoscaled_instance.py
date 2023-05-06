from pathlib import Path

# from aws_cdk import aws_param
from aws_cdk import aws_iam as iam
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_ssm as ssm
from constructs import Construct

THIS_DIR = Path(__file__).parent
RESOURCES_DIR = THIS_DIR / "resources"


class AutoscaledEc2InstanceProfile(Construct):
    """Role and instance profile for the EC2 instance that adds permission to access the S3 bucket."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        artifacts_bucket: s3.Bucket,
        **kwargs,
    ):
        super().__init__(scope=scope, id=construct_id, **kwargs)

        self.role = iam.Role(
            self,
            id="AutoScaledEC2InstanceRole",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
        )
        self.role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSSMManagedInstanceCore"))

        github_ssh_private_key = ssm.StringParameter.from_secure_string_parameter_attributes(
            self,
            id="ClearMLGithubSshPrivateKey",
            parameter_name="/clearml/github_ssh_private_key",
        )
        github_ssh_public_key = ssm.StringParameter.from_secure_string_parameter_attributes(
            self,
            id="ClearMLGithubSshPublicKey",
            parameter_name="/clearml/github_ssh_public_key",
        )

        artifacts_bucket.grant_read_write(self.role)
        github_ssh_private_key.grant_read(self.role)
        github_ssh_public_key.grant_read(self.role)
        add_policy_for_querying_athena(self.role)

        self.instance_profile = iam.CfnInstanceProfile(
            self,
            id="AutoScaledEC2InstanceProfile",
            roles=[self.role.role_name],
        )


def add_policy_for_querying_athena(role: iam.Role):
    role.add_to_policy(
        iam.PolicyStatement(
            actions=[
                "athena:StartQueryExecution",
                "athena:GetQueryExecution",
                "athena:GetQueryResults",
            ],
            resources=["*"],
        )
    )
