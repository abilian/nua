import json
import os
import shlex
import subprocess
import tempfile
from pathlib import Path

import tomli
from cleez import Command
from cleez.colors import bold, dim
from cleez.command import Argument

from ..client import get_client

client = get_client()

# Hardcoded for now
NUA_ENV = "/home/nua/env"
NUA_HOST = os.environ["NUA_HOST"]

EXCLUDES = [
    ".git",
    ".env",
    ".venv",
    ".cache",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".nox",
    ".tox",
    ".coverage",
    ".idea",
    "dist",
    "build",
    "data",
    "doc",
    "vite/node_modules/",
    "front-old",
    "tmp",
    "sandbox",
]


class BuildCommand(Command):
    """Build app but don't deploy it."""

    name = "build"

    def run(self):
        host = NUA_HOST
        config = get_config()
        app_id = config["metadata"]["id"]

        build_dir = tempfile.mkdtemp(prefix=f"nua-build-{app_id}-", dir="/tmp")  # noqa

        print(bold(f"Building app {app_id}..."))

        excludes_args = " ".join([f"--exclude={e}" for e in EXCLUDES])
        ssh(f"mkdir -p {build_dir}", host=host)
        sh(f"rsync -e ssh --delete-after -az {excludes_args} ./ nua@{host}:{build_dir}")

        ssh(f"{NUA_ENV}/bin/nua-build -vvv {build_dir}", host)

        print()


# @cli.command()
#
#     verbosity = 1 + verbose - quiet
#     verbosity_flags = verbosity * ["-v"]
#
#     if experimental:
#         typer.secho(
#             "Using experimental builder (from nua-dev).", fg=typer.colors.YELLOW
#         )
#         subprocess.run(["nua-dev", "build", path])
#     else:
#         subprocess.run(["nua-build"] + verbosity_flags + [path])
#


class DeployCommand(Command):
    """Deploy app."""

    name = "deploy"

    arguments = [
        Argument("domain", nargs="?", help="Domain to deploy to."),
    ]

    def run(self, domain=None):
        """Deploy all apps."""
        config = get_config()
        host = NUA_HOST

        app_id = config["metadata"]["id"]
        deploy_config = {
            "site": [
                {
                    "image": app_id,
                    "domain": domain,
                }
            ],
        }

        temp_dir = tempfile.mkdtemp(prefix=f"nua-deploy-{app_id}-", dir="/tmp")  # noqa
        config_file = Path(temp_dir) / "deploy.json"
        Path(config_file).write_text(json.dumps(deploy_config, indent=2))

        sh(f"rsync -az --mkpath {config_file} root@{host}:{config_file}")
        ssh(f"{NUA_ENV}/bin/nua-orchestrator deploy {config_file}", host)


#
# helpers
#
def sh(cmd: str, cwd: str = "."):
    """Run a shell command."""
    print(dim(f'Running "{cmd}" locally in "{cwd}"...'))
    args = shlex.split(cmd)
    try:
        subprocess.run(args, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {e.cmd}")


def ssh(cmd: str, host: str):
    """Run a ssh command."""
    print(dim(f'Running "{cmd}" on server...'))
    args = shlex.split(cmd)
    cmd = ["ssh", f"nua@{host}", f"{shlex.join(args)}"]  # type: ignore
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {e.cmd}")


def get_config() -> dict:
    config_file = Path("nua/nua-config.toml")
    config_data = config_file.read_text()
    return tomli.loads(config_data)
    # return toml.loads(config_data)
