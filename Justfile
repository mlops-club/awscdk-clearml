# This is a "Justfile". "just" is a task-runner similar to "make", but much less frustrating.
# There is a VS Code extension for just that provides syntax highlighting.
#
# Execute any commands in this file by running "just <command name>", e.g. "just install".

set dotenv-load := true

AWS_PROFILE := "mlops-tooling"
AWS_REGION := "us-west-2"


# install the project's python packages and other useful
install: require-venv
    # install useful VS Code extensions; configure VS Code settings
    which code && just install-recommended-vscode-extensions
    cp .vscode/example-settings.json settings.json || echo ".vscode/settings.json already present"

    python3 -m pip install --upgrade pip

    # install development utils
    which pre-commit || python3 -m pip install pre-commit
    which black || python3 -m pip install black
    which pylint || python3 -m pip install pylint
    which flake8 || python3 -m pip install flake8 Flake8-pyproject Flake8-docstrings
    which mypy || python3 -m pip install mypy

    # install the minecraft-deployment package as an "editable" package
    python3 -m pip install --editable .[all]

    # install pre-commit hooks to protect the quality of code committed by contributors
    pre-commit install

    # install node if npm not found
    which npm || (which brew && brew install node)
    which npm || (which apt-get && sudo apt-get install nodejs -y)

    # install aws cdk CLI if not found
    which cdk || npm install -g aws-cdk

    # install awscli if not found
    which aws || (which brew && brew install awscli)
    which aws || (which apt-get && sudo apt-get install awscli -y)


cdk-deploy: #require-venv
    AWS_PROFILE={{AWS_PROFILE}} \
    CDK_DEFAULT_REGION={{AWS_REGION}} \
    AWS_REGION={{AWS_REGION}} \
    cdk deploy \
        --all \
        --diff \
        --require-approval never \
        --profile {{AWS_PROFILE}} \
        --region {{AWS_REGION}} \
        --app "python app.py" # --hotswap

cdk-diff: #require-venv
    AWS_PROFILE={{AWS_PROFILE}} \
    AWS_ACCOUNT_ID=$(just get-aws-account-id) \
    CDK_DEFAULT_REGION={{AWS_REGION}} \
    AWS_REGION={{AWS_REGION}} \
    cdk diff \
        --profile {{AWS_PROFILE}} \
        --region {{AWS_REGION}} \
        --app "python3 app.py"

cdk-destroy: #require-venv
    AWS_PROFILE={{AWS_PROFILE}} \
    AWS_ACCOUNT_ID=`just get-aws-account-id` \
    CDK_DEFAULT_REGION={{AWS_REGION}} \
    cdk destroy --all --diff --profile {{AWS_PROFILE}} --region {{AWS_REGION}} --app "python3 app.py"

# generate CloudFormation from the code in "{{CDK_PLATFORM_DIR}}"
cdk-synth: require-venv login-to-aws
    AWS_PROFILE={{AWS_PROFILE}} \
    AWS_ACCOUNT_ID=$(just get-aws-account-id) \
    CDK_DEFAULT_REGION={{AWS_REGION}} \
    AWS_REGION={{AWS_REGION}} \
    cdk synth --all --profile mlops-club --app "python3 app.py"

open-aws:
    #!/bin/bash
    MLOPS_CLUB_SSO_START_URL="https://d-926768adcc.awsapps.com/start"
    open $MLOPS_CLUB_SSO_START_URL

# Ensure that an "mlops-club" AWS CLI profile is configured. Then go through an AWS SSO
# sign in flow to get temporary credentials for that profile. If this command finishes successfully,
# you will be able to run AWS CLI commands against the MLOps club account using '--profile mlops-club'
# WARNING: this login only lasts for 8 hours
login-to-aws:
    #!/bin/bash
    MLOPS_CLUB_AWS_PROFILE_NAME="mlops-club"
    MLOPS_CLUB_AWS_ACCOUNT_ID="630013828440"
    MLOPS_CLUB_SSO_START_URL="https://d-926768adcc.awsapps.com/start"
    MLOPS_CLUB_SSO_REGION="us-west-2"

    # TODO: make this check work so we can uncomment it. It will make it so we only have to
    # open our browser if our log in has expired or we have not logged in before.
    # skip if already logged in
    # aws sts get-caller-identity --profile ${MLOPS_CLUB_AWS_PROFILE_NAME} | cat | grep 'UserId' > /dev/null \
    #     && echo "[mlops-club] ✅ Logged in with aws cli" \
    #     && exit 0

    # configure an "[mlops-club]" profile in aws-config
    echo "[mlops-club] Configuring an AWS profile called '${MLOPS_CLUB_AWS_PROFILE_NAME}'"
    aws configure set sso_start_url ${MLOPS_CLUB_SSO_START_URL} --profile ${MLOPS_CLUB_AWS_PROFILE_NAME}
    aws configure set sso_region ${MLOPS_CLUB_SSO_REGION} --profile ${MLOPS_CLUB_AWS_PROFILE_NAME}
    aws configure set sso_account_id ${MLOPS_CLUB_AWS_ACCOUNT_ID} --profile ${MLOPS_CLUB_AWS_PROFILE_NAME}
    aws configure set sso_role_name AdministratorAccess --profile ${MLOPS_CLUB_AWS_PROFILE_NAME}
    aws configure set region ${MLOPS_CLUB_SSO_REGION} --profile ${MLOPS_CLUB_AWS_PROFILE_NAME}

    # login to AWS using single-sign-on
    aws sso login --profile ${MLOPS_CLUB_AWS_PROFILE_NAME} \
    && echo '' \
    && echo "[mlops-club] ✅ Login successful. AWS CLI commands will now work by adding the '--profile ${MLOPS_CLUB_AWS_PROFILE_NAME}' 😃" \
    && echo "             Your '${MLOPS_CLUB_AWS_PROFILE_NAME}' profile has temporary credentials using this identity:" \
    && echo '' \
    && aws sts get-caller-identity --profile ${MLOPS_CLUB_AWS_PROFILE_NAME} | cat

# throw an error if a virtual environment isn't activated;
# add this as a requirement to other targets that you want to ensure always run in
# some kind of activated virtual environment
require-venv:
    #!/usr/bin/env python3
    import sys
    from textwrap import dedent

    def get_base_prefix_compat():
        """Get base/real prefix, or sys.prefix if there is none."""
        return getattr(sys, "base_prefix", None) or getattr(sys, "real_prefix", None) or sys.prefix

    def in_virtualenv():
        return get_base_prefix_compat() != sys.prefix

    if not in_virtualenv():
        print(dedent("""\
            ⚠️ WARNING! 'just' detected that you have not activated a python virtual environment.

            To resolve this error, please activate a virtual environment by running
            whichever of the following commands apply to you:

            ```bash
            # create a (virtual) copy of the python just for this project
            python -m venv ./venv/

            # activate that copy of python (now 'which python' points to your new virtual copy)
            source ./venv/bin/activate

            # re-run whatever 'just' command you just tried to run, for example
            just install
            ```
        """))
    else:
        print("[mlops-club] ✅ Virtual environment is active")

# print the AWS account ID of the current AWS_PROFILE to stdout
get-aws-account-id:
    #!/usr/bin/env python3
    import json
    import subprocess

    args = ["aws", "sts", "get-caller-identity", "--profile", "{{AWS_PROFILE}}"]
    proc = subprocess.run(args, capture_output=True)

    aws_cli_response = json.loads(proc.stdout)
    print(aws_cli_response["Account"])

create-ec2-key-pair-from-personal-ssh-keys:
    #!/bin/bash
    AWS_REGION={{AWS_REGION}} \
    AWS_PROFILE={{AWS_PROFILE}} \
    aws ec2 import-key-pair \
        --key-name $(whoami) \
        --public-key-material fileb://~/.ssh/id_rsa.pub

# run quality checks and autoformatters against your code
lint: require-venv
    pre-commit run --all-files

clean:
    find . \
        -name "node_modules" -prune -false \
        -o -name "venv" -prune -false \
        -o -name ".git" -prune -false \
        -type d -name "*.egg-info" \
        -o -type d -name "dist" \
        -o -type d -name ".projen" \
        -o -type d -name "build_" \
        -o -type d -name "build" \
        -o -type d -name "cdk.out" \
        -o -type d -name ".mypy_cache" \
        -o -type d -name ".pytest_cache" \
        -o -type d -name "test-reports" \
        -o -type d -name "htmlcov" \
        -o -type d -name ".coverage" \
        -o -type d -name ".ipynb_checkpoints" \
        -o -type d -name "__pycache__" \
        -o -type f -name "coverage.xml" \
        -o -type f -name ".DS_Store" \
        -o -type f -name "*.pyc" \
        -o -type f -name "*cdk.context.json" | xargs rm -rf {}


install-recommended-vscode-extensions:
    code --force --install-extension ms-python.python \
         --force --install-extension ms-python.black-formatter \
         --force --install-extension ms-python.pylint \
         --force --install-extension ms-python.flake8 \
         --force --install-extension ms-python.vscode-pylance \
         --force --install-extension ms-python.isort \
         --force --install-extension skellock.just \
         --force --install-extension yzhang.markdown-all-in-one \
         --force --install-extension bungcip.better-toml \
         --force --install-extension eamodio.gitlens \
         --force --install-extension ms-azuretools.vscode-docker \
         --force --install-extension ms-vsliveshare.vsliveshare \
         --force --install-extension christian-kohler.path-intellisense

connect_to_host id region:
    aws ssm start-session --target {{id}} --region={{region}}

run-aws-autoscaler:
    python aws_autoscaler.py --config-file aws_autoscaler.yaml --run
