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
    generate_vagrantfile()

    if "running" in sh("vagrant status", capture=True):
        print("Vagrant is already running")
    else:
        sh("vagrant up --provider qemu")

    ssh("curl -L https://nua.rocks/install.py | sudo python3")


def generate_vagrantfile():
    proc = platform.processor()
    boxname = BOXES[proc]
    Path("Vagrantfile").write_text(
        Path("Vagrantfile.tpl").read_text().replace("##BOXNAME##", boxname)
    )


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


def ssh(cmd: str):
    """Run a ssh command."""
    print(dim(f'Running "{cmd}" on server...'))
    # args = shlex.split(cmd)
    cmd = ["vagrant", "ssh", "-c", cmd]  # type: ignore
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
