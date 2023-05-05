"""Boilerplate stack to make sure the CDK is set up correctly."""


from typing import Optional

import aws_cdk as cdk
from aws_cdk import Stack
from aws_cdk import aws_certificatemanager as acm
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_elasticloadbalancingv2 as elbv2
from aws_cdk import aws_elasticloadbalancingv2_targets as elbv2_targets
from aws_cdk import aws_route53 as route53
from aws_cdk import aws_route53_targets as route53_targets
from aws_cdk import aws_s3 as s3
from constructs import Construct

from cdk_clearml.ec2_instance import ClearMLServerEC2Instance


class ClearMLStack(Stack):
    """Everything needed to run the ClearML Server on AWS."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        top_level_domain_name: str,
        vpc_name: Optional[str] = None,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        vpc = ec2.Vpc.from_lookup(self, "VPC", vpc_name=vpc_name)
        clearml_instance = ClearMLServerEC2Instance(self, "ClearMLServerEC2Instance", vpc=vpc)

        artifact_bucket = s3.Bucket(
            self,
            "clearml-artifact-storage",
            versioned=False,
            encryption=s3.BucketEncryption.S3_MANAGED,
            # Change to retain for production.
            removal_policy=cdk.RemovalPolicy.DESTROY,
        )

        artifact_bucket.grant_read_write(clearml_instance.ec2_instance.role)

        # map_subdomain_to_ec2_ip(
        #     scope=self,
        #     ip_address=clearml_instance.ec2_instance.instance_public_ip,
        #     top_level_domain_name=top_level_domain_name,
        #     subdomain="app.clearml",
        # )
        # map_subdomain_to_ec2_ip(
        #     scope=self,
        #     ip_address=clearml_instance.ec2_instance.instance_public_ip,
        #     top_level_domain_name=top_level_domain_name,
        #     subdomain="files.clearml",
        # )
        # map_subdomain_to_ec2_ip(
        #     scope=self,
        #     ip_address=clearml_instance.ec2_instance.instance_public_ip,
        #     top_level_domain_name=top_level_domain_name,
        #     subdomain="api.clearml",
        # )

        alb = elbv2.ApplicationLoadBalancer(
            self,
            "ClearMLServerALB",
            vpc=vpc,
            internet_facing=False,
            security_group=clearml_instance.security_group,
        )

        hosted_zone = route53.HostedZone.from_lookup(
            self,
            "hosted-zone",
            domain_name=top_level_domain_name,
        )

        dns_validated_cert = acm.Certificate(
            self,
            "cert",
            domain_name=top_level_domain_name,
            subject_alternative_names=[
                f"*.{top_level_domain_name}",
                f"*.clearml.{top_level_domain_name}",
            ],
            validation=acm.CertificateValidation.from_dns(hosted_zone=hosted_zone),
        )

        # redirect http to https
        alb.add_redirect(
            source_protocol=elbv2.ApplicationProtocol.HTTP,
            target_protocol=elbv2.ApplicationProtocol.HTTPS,
            target_port=443,
            open=True,
        )

        # https://app.clearml -> ec2:8080
        # https://files.clearml -> ec2:8081
        # https://api.clearml -> ec2:8008

        https_listener = alb.add_listener(
            "listener",
            protocol=elbv2.ApplicationProtocol.HTTPS,
            certificates=[elbv2.ListenerCertificate(certificate_arn=dns_validated_cert.certificate_arn)],
            port=443,
            # default action is returning a 404
            default_action=elbv2.ListenerAction.fixed_response(
                status_code=404,
                content_type="text/plain",
                message_body="404 Not Found",
            ),
            # default_target_groups=[
            #     elbv2.ApplicationTargetGroup(
            #         scope,
            #         f"target-group",
            #         port=443,
            #         targets=[elbv2_targets.InstanceTarget(clearml_instance.ec2_instance)],
            #         protocol=elbv2.ApplicationProtocol.HTTP,
            #         vpc=vpc,
            #         health_check=elbv2.HealthCheck(
            #             enabled=True,
            #             port=str(8080),
            #             path="/",
            #             protocol=elbv2.Protocol.HTTP,
            #         ),
            #     )
            # ],
        )

        map_subdomain_to_alb_to_ec2(
            scope=self,
            alb=alb,
            top_level_domain_name=top_level_domain_name,
            subdomain="app.clearml",
            port=8080,
            https_listener=https_listener,
            ec2_vpc=vpc,
            ec2_instance=clearml_instance.ec2_instance,
            priority=1,
        )
        map_subdomain_to_alb_to_ec2(
            scope=self,
            alb=alb,
            top_level_domain_name=top_level_domain_name,
            subdomain="files.clearml",
            port=8081,
            https_listener=https_listener,
            ec2_vpc=vpc,
            ec2_instance=clearml_instance.ec2_instance,
            priority=2,
        )
        map_subdomain_to_alb_to_ec2(
            scope=self,
            alb=alb,
            top_level_domain_name=top_level_domain_name,
            subdomain="api.clearml",
            port=8008,
            https_listener=https_listener,
            ec2_vpc=vpc,
            ec2_instance=clearml_instance.ec2_instance,
            priority=3,
        )


def map_subdomain_to_alb_to_ec2(
    scope: Construct,
    alb: elbv2.ApplicationLoadBalancer,
    top_level_domain_name: str,
    ec2_instance: ec2.Instance,
    ec2_vpc: str,
    subdomain: str,
    port: int,
    https_listener: elbv2.ApplicationListener,
    priority: int,
) -> None:
    """
    Map a subdomain to an Application Load Balancer.

    `<subdomain>.<top-level-domain> -> ALB -> <ec2-instance>:<port>`
    """
    subdomain_id_string = subdomain.replace(".", "-")
    fully_qualified_subdomain = f"{subdomain}.{top_level_domain_name}"

    hosted_zone = route53.HostedZone.from_lookup(
        scope,
        f"{subdomain_id_string}-hosted-zone",
        domain_name=top_level_domain_name,
    )

    # map the subdomain to the ALB
    route53.ARecord(
        scope,
        f"{subdomain_id_string}-alb-record",
        zone=hosted_zone,
        target=route53.RecordTarget.from_alias(route53_targets.LoadBalancerTarget(alb)),
        record_name=fully_qualified_subdomain,
    )

    target_group = elbv2.ApplicationTargetGroup(
        scope,
        f"{subdomain_id_string}-target-group",
        port=port,
        targets=[elbv2_targets.InstanceTarget(ec2_instance)],
        protocol=elbv2.ApplicationProtocol.HTTP,
        vpc=ec2_vpc,
        health_check=elbv2.HealthCheck(
            enabled=True,
            port=str(8080),
            path="/",
            protocol=elbv2.Protocol.HTTP,
        ),
    )

    # route to this target group if the host begins with the subdomain
    https_listener.add_action(
        f"{subdomain_id_string}-listener-action",
        conditions=[
            elbv2.ListenerCondition.host_headers(
                values=[fully_qualified_subdomain],
            )
        ],
        priority=priority,
        action=elbv2.ListenerAction.forward(
            target_groups=[target_group],
        ),
    )
