#!/usr/bin/env python3

"""Installer script for Nua Orchestrator.

Should be run as:

```
curl https://nua.rocks/install.py | sudo python3
# or
curl https://github.com/abilian/nua/raw/main/installer/install.py | sudo python3
```
"""
import argparse
import os
import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path

HOME = os.environ["HOME"]

DEBIAN_PACKAGES = [
    "curl",
    "python3.10",
    "python3.10-venv",
    "python3.10-dev",
    "python3-pip",
    "pipx",
]

APT_CONF = """
Acquire::http {No-Cache=True;};
APT::Install-Recommends "0";
APT::Install-Suggests "0";
Acquire::GzipIndexes "true";
Acquire::CompressionTypes::Order:: "gz";
Dir::Cache { srcpkgcache ""; pkgcache ""; }
"""

DIM = "\033[2m"
RESET = "\033[0m"


@dataclass(frozen=True)
class Installer:
    verbosity: int

    def run(self):
        self.prepare_server()
        self.install_base_packages()
        self.install_pipx_packages()
        self.run_nua_bootstrap()

    def prepare_server(self):
        """Prepare the server."""
        Path("/etc/apt/apt.conf.d/00-nua").write_text(APT_CONF)

        sh("apt-get update -q")
        sh("apt-get upgrade -y")

    def install_base_packages(self):
        """Install base packages."""
        sh("apt-get update")
        packages = " ".join(DEBIAN_PACKAGES)
        sh(f"apt-get install -y {packages}")

    def install_pipx_packages(self):
        """Install pipx packages."""
        sh("pipx install nua-orchestrator")

    def run_nua_bootstrap(self):
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
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-v", "--verbosity", action="count", help="Increase output verbosity"
    )
    args = parser.parse_args()
    installer = Installer(args.verbosity or 0)
    installer.run()
