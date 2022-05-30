#!/bin/env python3

import logging
import os
import sys
from pathlib import Path

import fire
import rich.console
import toml

logging.basicConfig(level=logging.INFO)

console = rich.console.Console()


config = toml.load(open("nua-config.toml"))
version = config["metadata"].get("version")
src_url = config["build"].get("src_url")
if "{" in src_url and version:
    src_url = src_url.format(version=version)


def build():
    sh("pip list")

    cmd = f"curl -sL {src_url} | tar -xz --strip-components 1 -f -"
    sh(cmd)

    if Path("requirements.txt").exists():
        build_python()


def build_python():
    sh("python3 -m venv /nua/env")
    sh("/nua/env/bin/pip install -r requirements.txt")


def sh(cmd):
    print(cmd)
    status = os.system(cmd)
    if status != 0:
        print("Something whent wrong")
        sys.exit(status)


def main():
    fire.Fire(build)


if __name__ == "__main__":
    main()
