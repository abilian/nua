#!/usr/bin/env python3

import argparse
import platform
import shlex
import subprocess
from pathlib import Path

DIM = "\033[2m"
RESET = "\033[0m"
RED = "\033[31m"

BOXES = {
    "x86_64": "generic/ubuntu2204",
    "arm": "perk/ubuntu-2204-arm64",
}


def main():
    sh("mkdir -p apps")
    sh("cp -r ../../apps/real-apps/* apps/")

    generate_vagrantfile()
    vagrant_up()
    ssh("curl -L https://nua.rocks/install.py | sudo python3")

    ssh("sudo cp -r .ssh /home/nua/")
    ssh("sudo chown -R nua.nua /home/nua/.ssh")

    for app_dir in Path("apps").iterdir():
        app_name = app_dir.name
        ssh(
            f"cd /vagrant/apps/{app_name} && /home/nua/env/bin/nua-build -vv",
            user="nua",
        )


def generate_vagrantfile():
    proc = platform.processor()
    boxname = BOXES[proc]
    Path("Vagrantfile").write_text(
        Path("Vagrantfile.tpl").read_text().replace("##BOXNAME##", boxname)
    )


def vagrant_up():
    if "running" in sh("vagrant status", capture=True):
        print("Vagrant is already running")
        return

    if platform.system() == "Darwin":
        sh("vagrant up --provider qemu")
    else:
        sh("vagrant up")

    ssh_config = sh("vagrant ssh-config", capture=True)
    Path("ssh-config").write_text(ssh_config)


def sh(cmd: str, cwd: str = ".", capture=False) -> str:
    """Run a shell command."""
    if cwd == ".":
        print(dim(f'Running "{cmd}" locally...'))
    else:
        print(dim(f'Running "{cmd}" locally in "{cwd}"...'))
    args = shlex.split(cmd)
    opts = {
        "check": True,
        "cwd": cwd,
        "capture_output": capture,
        "text": True,
    }
    try:
        result = subprocess.run(args, **opts)
        return result.stdout  # type: ignore
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {e.cmd}")


def ssh(cmd: str, user="vagrant"):
    """Run a ssh command."""
    if user == "vagrant":
        print(dim(f'Running "{cmd}" on vagrant...'))
    else:
        print(dim(f'Running "{cmd}" on vagrant as "{user}"...'))

    # args = shlex.split(cmd)
    cmd = ["ssh", "-F", "ssh-config", f"{user}@default", cmd]  # type: ignore
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {e.cmd}")


def dim(text: str) -> str:
    """Return dimmed text."""
    return f"{DIM}{text}{RESET}"


def red(text: str) -> str:
    """Return red text."""
    return f"{RED}{text}{RESET}"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", nargs="?", help="Command to run")
    args = parser.parse_args()
    command = args.command
    match command:
        case "main" | None:
            main()
        case _:
            print(red(f"Unknown command {command}"))
