import subprocess
from textwrap import dedent

from clearml import Task

SCRIPT = dedent(
    """\
    set -x

    ls -la /.ssh
    ls -la ~/.ssh
    whoami
    cat ~/.ssh/id_rsa | head -n 3

    mkdir -p /home/$(whoami)/.ssh
    cp ~/.ssh/id_rsa* /home/$(whoami)/.ssh/

    ssh-keyscan github.com >> ~/.ssh/known_hosts
    git clone git@github.com:phitoduck/awscdk-clearml.git ./awscdk-clearml__
    """
)
task = Task.init(project_name="Hello World", task_name="Eric")
# task.set_base_docker(docker_setup_bash_script=SCRIPT)


# run the script as a subprocess and print its output
def run_shell_script(script: str):
    process = subprocess.Popen(
        script,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )
    stdout, stderr = process.communicate()
    print(stdout)
    print(stderr)


# run_shell_script(SCRIPT)

task.execute_remotely(
    queue_name="aws_4gpu_machines",
    exit_process=True,
)
