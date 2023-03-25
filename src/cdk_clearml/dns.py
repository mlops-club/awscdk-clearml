from aws_cdk import aws_route53 as route53
from constructs import Construct


def map_subdomain_to_ec2_ip(
    scope: Construct,
    ip_address: str,
    top_level_domain_name: str,
    subdomain: str,
) -> None:
    """Map a subdomain to the ClearML server's IP address."""
    fully_qualified_subdomain = f"{subdomain}.{top_level_domain_name}"
    a_record_id = fully_qualified_subdomain.replace(".", "")

    hosted_zone = route53.HostedZone.from_lookup(
        scope=scope,
        id=f"{a_record_id}-ClearMLHostedZone",
        domain_name=top_level_domain_name,
    )

    route53.ARecord(
        scope=scope,
        id=f"{a_record_id}-ARecord",
        zone=hosted_zone,
        record_name=fully_qualified_subdomain,
        target=route53.RecordTarget.from_ip_addresses(ip_address),
    )
