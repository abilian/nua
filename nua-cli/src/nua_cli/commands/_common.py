import os
import shlex
import subprocess
from pathlib import Path

import tomli
from cleez.colors import dim

# Hardcoded for now
NUA_ENV = "/home/nua/env"
ORCH_PATH = "/home/nua/env/bin/nua-orchestrator"


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
    config_file = Path("nua-config.toml")
    if not config_file.exists():
        config_file = Path("nua/nua-config.toml")
    config_data = config_file.read_text()
    return tomli.loads(config_data)


def get_nua_host() -> str:
    """Return the nua host."""
    return os.environ.get("NUA_HOST", "localhost")


def get_nua_user() -> str:
    """Return the nua user on the Nua host."""
    return os.environ.get("NUA_USER", "nua")
