import os

from aws_cdk import App, Environment
from rich import print

from cdk_clearml.stack import ClearMLStack
from cdk_clearml.utils.aws_account_info import get_aws_account_id

AWS_ACCOUNT_ID: str = get_aws_account_id()
CDK_ENV = Environment(account=AWS_ACCOUNT_ID, region=os.getenv("AWS_REGION", "us-west-2"))

print("App settings")
print(
    {
        "AWS_ACCESS_KEY_ID": "set" if os.getenv("AWS_ACCESS_KEY_ID") else "unset",
        "AWS_SECRET_ACCESS_KEY": "set" if os.getenv("AWS_SECRET_ACCESS_KEY") else "unset",
        "AWS_PROFILE": os.getenv("AWS_PROFILE", "unset"),
        "AWS_ACCOUNT_ID": AWS_ACCOUNT_ID,
        "AWS_REGION": CDK_ENV.region,
    }
)

APP = App()

ClearMLStack(
    APP,
    "clearml-2",
    top_level_domain_name="mlops-tools.ai.muyben.tech",
    # vpc_name="MlOpsMLFlowCDKStack/fMlOpsMLFlowCDKStack-vpc",
    vpc_name="ben-networked-vpc",
    env=CDK_ENV,
)

APP.synth()
