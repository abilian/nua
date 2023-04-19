#!/usr/bin/env python3

"""Installer script for Nua Orchestrator.

Should be run as:

```
curl https://nua.rocks/install.py | sudo python3
# or
curl https://github.com/abilian/nua/raw/main/installer/install.py | sudo python3
```
"""

import os
import shlex
import subprocess

HOME = os.environ["HOME"]

DEBIAN_PACKAGES = [
    "python3.10",
    "python3.10-venv",
    "python3.10-dev",
    "python3-pip",
    "pipx",
]

DIM = "\033[2m"
RESET = "\033[0m"


def main():
    install_base_packages()
    install_pipx_packages()
    run_nua_bootstrap()


def install_base_packages():
    """Install base packages."""
    sh("apt-get update")
    packages = " ".join(DEBIAN_PACKAGES)
    sh(f"apt-get install -y {packages}")


def install_pipx_packages():
    """Install pipx packages."""
    sh("pipx install nua-orchestrator")


def run_nua_bootstrap():
    """Run nua-bootstrap."""
    sh(f"{HOME}/.local/bin/nua-bootstrap")


#
# Util
#
def sh(cmd: str, cwd: str = "."):
    """Run a shell command."""
    if cwd == ".":
        print(dim(f'Running "{cmd}" locally...'))
    else:
        print(dim(f'Running "{cmd}" locally in "{cwd}"...'))
    args = shlex.split(cmd)
    env = os.environ.copy()
    env["DEBIAN_FRONTEND"] = "noninteractive"
    try:
        subprocess.run(args, check=True, env=env, cwd=cwd)
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {e.cmd}")


def dim(text: str) -> str:
    """Return dimmed text."""
    return f"{DIM}{text}{RESET}"


if __name__ == "__main__":
    main()
