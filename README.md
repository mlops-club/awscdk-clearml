# `awscdk-clearml` 🧱

[![MPL 2.0](https://img.shields.io/badge/license-MPL%202.0-blue.svg?style=for-the-badge)](./LICENSE.txt)

The goal of this project is to make a single pip-installable package that allows anyone to provision
an opinionated ClearML deployment on AWS.

<!-- hrefs to images are absolute URLs to GitHub so that they work on PyPI -->

<!-- <figure style="width: 500px; text-align: center;">
<p style="padding: 10px">Login</p>
<img src="https://github.com/mlops-club/awscdk-minecraft/blob/trunk/docs/ui/hosted-ui.png?raw=true" style="width: 100%;"/>
</figure> -->


## Usage

### Prerequisites

- Create these as `SecureString` parameters in the AWS Systems Manager Parameter 
  -  `/clearml/github_ssh_private_key`, from `cat ~/.ssh/id_rsa | pbcopy`
  -  `/clearml/github_ssh_public_key`, from `cat ~/.ssh/id_rsa.pub | pbcopy`
- Create an SSH key for yourself
  - `just install create-ec2-key-pair-from-personal-ssh-keys`

### (1) Be sure to have the the following installed:

- [Python](https://www.python.org/downloads/) 3.8 or higher
- [NodeJS](https://nodejs.org/en/download/) 14 or higher (a dependency of the AWS CDK CLI)
- [AWS CDK CLI](https://docs.aws.amazon.com/cdk/latest/guide/cli.html)
- [Docker](https://docs.docker.com/get-docker/) (should be installed and *running*)

### (2) Install the AWS CDK stack exposed by this package

```bash
pip install awscdk-clearml
```

### (3) Use it in your CDK app

```python
# app.py
import os

from aws_cdk import App, Environment
from cdk_clearml import ClearMLStack

APP = App()

# TBD ...

APP.synth()
```

> Note: `app.py` is an AWS Cloud Development Kit concept. If you are not familiar with
> AWS CDK and what an `app.py` file is, you can read more about it in the [AWS CDK docs](https://aws.amazon.com/cdk/).


## Contributing

This project started as a Hackathon on March 24, 2023.

Contributors can expect to come away with an enviable amount of real-world cloud architecture
experience :D

## Useful links

> 💡 Click the images to go to each collaboration tool.

> 💡 Bookmark this repository so you can get quick access to these links.

|                                                                                                                                                                                                                                                                                                                                  |                                                                                                                                                                                                                                                                                                                                                          |
| :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------: | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------: |
|     <a href="https://app.gather.town/app/POdppw6MwFaG2D4k/MLOps%20Hackathon" target="_blank"><img style="float: left; width:  300px; height: 100%; background-size: cover;" src="https://github.com/mlops-club/awscdk-minecraft/blob/trunk/docs/gather-town.png?raw=true"></a>  <br/>Our virtual park (audio/screen sharing)     |            <a href="https://join.slack.com/t/mlopsclub/shared_invite/zt-1mzj3hxgy-_q5tjwBOzk3qsoB_uqf42A" target="_blank"><img style="float: left; width:  300px; height: 100%; background-size: cover;" src="https://github.com/mlops-club/awscdk-minecraft/blob/trunk/docs/slack.png?raw=true"></a> <br/>Slack, in the `#hackathon` channel            |
| <a href="https://www.figma.com/file/05tXuPdZHtqIzMjILwEsGW/MLOps-Hackathon?node-id=0%3A1&t=0HYhBvHp8WJ57eDw-1" target="_blank"><img style="float: left; width:  300px; height: 100%; background-size: cover;" src="https://github.com/mlops-club/awscdk-minecraft/blob/trunk/docs/roadmap.png?raw=true"></a> <br/>Roadmap, tasks | <a href="https://www.figma.com/file/7H1BQw5yffdGNUESnlaUvn/MLOps-Hackathon-(Architecture)?node-id=0%3A1&t=ZdLLOJHEqUJjXMpy-1" target="_blank"><img style="float: left; width:  300px; height: 100%; background-size: cover;" src="https://github.com/mlops-club/awscdk-minecraft/blob/trunk/docs/figma-architecture.png?raw=true"></a> <br/>Architecture |
|                <a href="https://d-926768adcc.awsapps.com/start" target="_blank"><img style="float: left; width:  300px; height: 100%; background-size: cover;" src="https://github.com/mlops-club/awscdk-minecraft/blob/trunk/docs/aws-console-login.png?raw=true"></a> <br/>`mlops-club` AWS account login page                 |                               <a href="https://github.com/mlops-club/awscdk-minecraft/blob/trunk" target="_blank"><img style="float: left; width:  300px; height: 100%; background-size: cover;" src="https://github.com/mlops-club/awscdk-minecraft/blob/trunk"></a> <br/>Similar project with reference code / resources                               |

### How do I run this project locally?

TL;DR, install `node` and `just`.

```
# install "just"; it's like "make", but less frustrating
brew install just

# install the project's python packages and pre-commit
just install
```

Alternatively, without `brew`:
```
curl --proto '=https' --tlsv1.2 -sSf https://just.systems/install.sh | bash -s -- --to <DEST IN YOUR PATH>
```

where `DEST IN YOUR PATH` refers to a directory that is present in your `$PATH` environment variable. For example, you might have in your `~/.bashrc` the line `PATH=~/bin:$PATH` to look for programs in `~/bin` first, which would be the "DEST" supplied above.

You also need `node` to execute any code related to AWS CDK, which you can install with `brew install nvm` and `nvm install 18`.

### How do I add code?

#### Branching strategy: trunk-based development with feature branches

We use pull requests. Create new branches based on `trunk` for experimentation, then open a PR for it.
You don't have to wait until you want to merge code to open a PR. For this project, the main purpose of doing PRs
is to share knowledge and get early feedback on your ideas.

#### Linting

Passing the `pre-commit` checks isn't a huge deal. They are mostly for your own benefit to prevent you
committing things to the repo that you don't want. You can always override `pre-commit` by running

```bash
# run all of the quality checking tools against your code
just lint
```

```bash
# skip the quality checking tools locally
git commit -m "I really want to commit this large file" --no-verify
```

#### Git configuration

> 📌 Note: you may want to use a different email/username for this repository than
> you typically use on your development machine. You can set your git settings locally
> like so:

```bash
git config --local user.email my-personal-email@gmail.com
git config --local user.user my-github-username
```
#### Notes on commits

DON'T COMMIT...

- credentials. Feel free to put them in a `.env` file, but make sure it's gitignored!
- large files (large CSV, ML model weights, C binaries, video, etc.)
  use git LFS rather than committing it directly.
- unformatted code

The pre-commit hooks setup for this repo when you ran `just install` will remind you
about these each time you commit :)
