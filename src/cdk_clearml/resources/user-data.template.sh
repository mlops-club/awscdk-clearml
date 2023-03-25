#!/bin/bash

# TODO: consider using try/catch expressions as shown in this SO answer: https://stackoverflow.com/questions/22009364/is-there-a-try-catch-command-in-bash
# to return a failure cfn-signal or success.

# This script is a templated string. All occurreces of "[dollar sign]<some var name>" will be substituted
# with other values by the CDK code.

# make the logged output of this user-data script available in the EC2 console
exec > >(tee /var/log/user-data.log | logger -t user-data -s 2>/dev/console) 2>&1

# print the commands this script runs as they are executed
set -x

# run the cfn-init to fetch files, this populates the docker-compose.yml, clearml.conf, and other files
yum install -y aws-cfn-bootstrap
/opt/aws/bin/cfn-init -v --stack $STACK_NAME --resource $LOGICAL_EC2_INSTANCE_RESOURCE_ID --region $AWS_REGION

export WORKDIR=/clearml
mkdir -p "$$WORKDIR"
cd "$$WORKDIR"

function install_and_run_clearml() {

    #########################################
    # --- Install CLI tool dependencies --- #
    #########################################

    yum update -y
    yum install -y docker

    # install docker-compose and make the binary executable
    curl -L https://github.com/docker/compose/releases/latest/download/docker-compose-$$(uname -s)-$$(uname -m) -o /usr/bin/docker-compose
    chmod +x /usr/bin/docker-compose

    # initialize docker and docker-swarm daemons
    service docker start

    # install aws cli
    yum install -y python38 python38-pip
    pip3 install awscli --upgrade --user

    # login to ECR and pull the minecraft server backup/restore image
    # aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"
    # docker pull "$BACKUP_SERVICE_DOCKER_IMAGE_URI"

    # restore from backup if $RESTORE_FROM_MOST_RECENT_BACKUP is set to "true"
    # if [ "$RESTORE_FROM_MOST_RECENT_BACKUP" = "true" ]; then
    #     docker-compose run minecraft-backup restore || echo "Failed to restore from backup. Starting fresh..."
    #     docker network rm minecraft-server
    # fi

    ############################################
    # --- Start up the with docker compose --- #
    ############################################

    # create volumes used by docker-compose
    mkdir -p "$$WORKDIR/opt/clearml/logs"
    mkdir -p "$$WORKDIR/opt/clearml/config"
    mkdir -p "$$WORKDIR/opt/clearml/data/fileserver"
    mkdir -p "$$WORKDIR/opt/clearml/data/elastic_7"
    mkdir -p "$$WORKDIR/usr/share/elasticsearch/logs"
    mkdir -p "$$WORKDIR/opt/clearml/logs"
    mkdir -p "$$WORKDIR/opt/clearml/data/fileserver"
    mkdir -p "$$WORKDIR/opt/clearml/config"
    mkdir -p "$$WORKDIR/opt/clearml/data/mongo_4/db"
    mkdir -p "$$WORKDIR/opt/clearml/data/mongo_4/configdb"
    mkdir -p "$$WORKDIR/opt/clearml/data/redis"
    mkdir -p "$$WORKDIR/opt/clearml/logs"
    mkdir -p "$$WORKDIR/opt/clearml/agent"

    # certain containers were failing due to not having sufficient file permissions
    chmod -R 777 "$$WORKDIR"
    docker-compose -f "$$WORKDIR/docker-compose.clear-ml.yml" up -d

}

# cfn-
install_and_run_clearml || /opt/aws/bin/cfn-signal -e 1 --stack $${AWS::StackName} --resource EC2Instance --region $${AWS::Region}
