"""Shell commands wrapped in Python."""
from invoke import task
from invoke.context import Context


@task
def install(context: Context):
    """Install dependencies required for the project repository."""
    # upgrade pip
    context.run("python3 -m pip install --upgrade pip")

    # install pip packages
    context.run("which pre-commit || python3 -m pip install pre-commit")
    context.run("which black || python3 -m pip install black")
    context.run("which pylint || python3 -m pip install pylint")
    context.run(
        "which flake8 || \
        python3 -m pip install flake8 Flake8-pyproject Flake8-docstrings"
    )
    context.run("which mypy || python3 -m pip install mypy")
    context.run("which invoke || python3 -m pip install invoke")

    # install npm packages
    context.run("which npm || (which brew && brew install node)")
    context.run(
        "which npm || \
                (which apt-get && sudo apt-get install nodejs -y)"
    )
    context.run("which cdk || npm install -g aws-cdk")

    # install AWS Command Line Interface (AWS CLI)
    context.run("which aws || (which brew && brew install awscli)")
    context.run(
        "which aws || \
                (which apt-get && sudo apt-get install awscli -y)"
    )
