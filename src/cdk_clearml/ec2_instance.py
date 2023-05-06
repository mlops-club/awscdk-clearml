from pathlib import Path
from string import Template
from typing import Optional

import aws_cdk as cdk
from aws_cdk import Stack
from aws_cdk import aws_cloudwatch as cloudwatch
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_ecr as ecr
from aws_cdk import aws_iam as iam
from aws_cdk import aws_s3 as s3
from constructs import Construct

from cdk_clearml.ec2_autoscaled_instance import AutoscaledEc2InstanceProfile

THIS_DIR = Path(__file__).parent
DOCKER_COMPOSE_FPATH = THIS_DIR / "resources/docker-compose.yml"
USER_DATA_TEMPLATE_FPATH = THIS_DIR / "resources/user-data.template.sh"


def render_user_data_script(
    docker_compose_yaml_contents: str,
    aws_account_id: str,
    aws_region: str,
    stack_name: str,
    logical_ec2_instance_resource_id: str,
    cfn_wait_handle: str,
):
    """Render the user data script using a templated string."""
    user_data_template = USER_DATA_TEMPLATE_FPATH.read_text(encoding="utf-8")

    # use templated string to substitute CLEARML_DOCKER_COMPOSE_YAML_CONTENTS in
    # the user data script
    template = Template(user_data_template)
    return template.substitute(
        {
            "CLEARML_DOCKER_COMPOSE_YAML_CONTENTS": docker_compose_yaml_contents,
            "AWS_ACCOUNT_ID": aws_account_id,
            "AWS_REGION": aws_region,
            "STACK_NAME": stack_name,
            "LOGICAL_EC2_INSTANCE_RESOURCE_ID": logical_ec2_instance_resource_id,
            "BACKUP_SERVICE_DOCKER_IMAGE_URI": "<todo: get this from ECR>",
            "RESTORE_FROM_MOST_RECENT_BACKUP": "<todo: implement this functionality>",
            "CFN_WAIT_HANDLE": cfn_wait_handle,
        }
    )


class ClearMLServerEC2Instance(Construct):
    """
    EC2 instance running ClearML Server.

    Docs for deploying ClearML to EC2 are here: https://clear.ml/docs/latest/docs/deploying_clearml/clearml_server_aws_ec2_ami/
    We're not using one of the pre-built AMI's.

    :param scope: The scope of the stack.
    :param construct_id: The ID of the stack.
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        vpc: Optional[ec2.Vpc] = None,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # we should prefer the default VPC to save money
        vpc = vpc or ec2.Vpc.from_lookup(scope=self, id="DefaultVPC", is_default=True)
        self.security_group = create_clearml_security_group(self, vpc=vpc)

        # enable SSH connection using AWS SSM (so users do not need SSH keys to access the instance)
        iam_role = iam.Role(
            scope=self,
            id="ClearMLServerIamRole",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
        )
        iam_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSSMManagedInstanceCore"))

        stack = Stack.of(self)

        # create a CfnWaitHandle
        cfn_wait_handle = cdk.CfnWaitConditionHandle(scope=self, id="CfnWaitHandle")

        self.subnet_selection = ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS)

        self.ec2_instance = ec2.Instance(
            scope=self,
            id="ClearMLServerInstance",
            vpc=vpc,
            instance_type=ec2.InstanceType("t2.medium"),
            machine_image=ec2.MachineImage.latest_amazon_linux(),
            user_data_causes_replacement=True,
            role=iam_role,
            security_group=self.security_group,
            init=ec2.CloudFormationInit.from_elements(
                # docker-compose file at /clearml/docker-compose.clearml.yml
                ec2.InitFile.from_string(
                    "/clearml/docker-compose.clear-ml.yml",
                    DOCKER_COMPOSE_FPATH.read_text(encoding="utf-8"),
                )
            ),
            key_name="ericriddoch",
            vpc_subnets=self.subnet_selection,
            # vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
        )

        # the logical ID is needed by the cfn-init command so it can grab the docker-compose file
        ec2_logical_resource_id = stack.get_logical_id(element=self.ec2_instance.node.default_child)

        user_data_contents: str = render_user_data_script(
            docker_compose_yaml_contents=DOCKER_COMPOSE_FPATH.read_text(encoding="utf-8"),
            aws_account_id=stack.account,
            aws_region=stack.region,
            stack_name=stack.stack_name,
            logical_ec2_instance_resource_id=ec2_logical_resource_id,
            cfn_wait_handle=cfn_wait_handle.logical_id,
        )

        self.ec2_instance.user_data.add_commands(user_data_contents)

        # # assign elastic IP address to the instance
        # ec2.CfnEIP(
        #     scope=self,
        #     id="ClearMLServerElasticIp",
        #     domain="vpc",
        #     instance_id=self.ec2_instance.instance_id,
        # )

        # add stack output for ip address of the ec2 instance
        cdk.CfnOutput(
            scope=self,
            id="ClearMLServerPrivateIp",
            value=self.ec2_instance.instance_private_ip,
            description="The public IP address of the ClearML server",
        )

        add_cloudwatch_alarms_to_ec2(scope=self, ec2_instance_id=self.ec2_instance.instance_id)


def create_clearml_security_group(scope: Construct, vpc: ec2.Vpc):
    # set up security group to allow inbound traffic on port 25565 for anyone
    security_group = ec2.SecurityGroup(
        scope=scope,
        id="ClearMLServerSecurityGroup",
        vpc=vpc,
        allow_all_outbound=True,
    )

    security_group.add_ingress_rule(
        peer=ec2.Peer.any_ipv4(),
        connection=ec2.Port.tcp(8080),
        description="ClearML Web UI",
    )
    security_group.add_ingress_rule(
        peer=ec2.Peer.any_ipv4(),
        connection=ec2.Port.tcp(8008),
        description="ClearML API Server",
    )
    security_group.add_ingress_rule(
        peer=ec2.Peer.any_ipv4(),
        connection=ec2.Port.tcp(8081),
        description="ClearML File Server",
    )

    security_group.add_ingress_rule(
        peer=ec2.Peer.any_ipv4(),
        connection=ec2.Port.tcp(22),
        description="Allow inbound traffic on port 22",
    )

    # allow all outbound traffic
    security_group.add_egress_rule(
        peer=ec2.Peer.any_ipv4(),
        connection=ec2.Port.all_traffic(),
        description="Allow all outbound traffic",
    )

    return security_group


def grant_ecr_pull_access(ecr_repo_arn: str, role: iam.Role, repo_construct_id: str):
    """Grant the given role access to pull docker images from the given ECR repo."""
    ecr_repo = ecr.Repository.from_repository_arn(scope=role, id=repo_construct_id, repository_arn=ecr_repo_arn)
    ecr_repo.grant_pull(role)


def grant_s3_read_write_access(bucket_name: str, role: iam.Role, bucket_construct_id: str):
    """Grant the given role read/write access to the given S3 bucket."""
    bucket = s3.Bucket.from_bucket_name(scope=role, id=bucket_construct_id, bucket_name=bucket_name)
    bucket.grant_read_write(role)


def add_cloudwatch_alarms_to_ec2(scope: Construct, ec2_instance_id: str) -> None:
    """Add alarms to the ec2 instance."""
    cloudwatch.Alarm(
        scope=scope,
        id="ClearMLServerCpuAlarm",
        metric=cloudwatch.Metric(
            namespace="AWS/EC2",
            metric_name="CPUUtilization",
            dimensions_map={"InstanceId": ec2_instance_id},
            statistic="Average",
            period=cdk.Duration.minutes(1),
        ),
        comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
        threshold=80,
        evaluation_periods=1,
        treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING,
        alarm_description="Alarm if CPU usage is greater than 80% for 1 minute",
    )

    cloudwatch.Alarm(
        scope=scope,
        id="ClearMLServerMemoryAlarm",
        metric=cloudwatch.Metric(
            namespace="System/Linux",
            metric_name="MemoryUtilization",
            dimensions_map={"InstanceId": ec2_instance_id},
            statistic="Average",
            period=cdk.Duration.minutes(1),
        ),
        comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
        threshold=80,
        evaluation_periods=1,
        treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING,
        alarm_description="Alarm if memory usage is greater than 80% for 1 minute",
    )

    cloudwatch.Alarm(
        scope=scope,
        id="ClearMLServerDiskAlarm",
        metric=cloudwatch.Metric(
            namespace="System/Linux",
            metric_name="DiskSpaceUtilization",
            dimensions_map={"InstanceId": ec2_instance_id},
            statistic="Average",
            period=cdk.Duration.minutes(1),
        ),
        comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
        threshold=80,
        evaluation_periods=1,
        treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING,
        alarm_description="Alarm if disk usage is greater than 80% for 1 minute",
    )

    cloudwatch.Alarm(
        scope=scope,
        id="ClearMLServerNetworkAlarm",
        metric=cloudwatch.Metric(
            namespace="System/Linux",
            metric_name="NetworkIn",
            dimensions_map={"InstanceId": ec2_instance_id},
            statistic="Average",
            period=cdk.Duration.minutes(1),
        ),
        comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
        threshold=80,
        evaluation_periods=1,
        treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING,
        alarm_description="Alarm if network usage is greater than 80% for 1 minute",
    )

    cloudwatch.Alarm(
        scope=scope,
        id="ClearMLServerOpenConnectionsAlarm",
        metric=cloudwatch.Metric(
            namespace="System/Linux",
            metric_name="NetworkIn",
            dimensions_map={"InstanceId": ec2_instance_id},
            statistic="Average",
            period=cdk.Duration.minutes(1),
        ),
        comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
        threshold=80,
        evaluation_periods=1,
        treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING,
        alarm_description="Alarm if number of open connections is greater than 80% for 1 minute",
    )


# if __name__ == "__main__":
#     print(
#         render_user_data_script(
#             docker_compose_yaml_contents=DOCKER_COMPOSE_FPATH.read_text(encoding="utf-8"),
#             aws_account_id="hi",
#             aws_region="hi",
#         )
#     )
