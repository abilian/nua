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


class Config:
    def __init__(self, filename="nua-config.toml"):
        self.data = toml.load(open(filename))

    def __getitem__(self, key):
        return self.data[key]

    @property
    def version(self):
        return self["metadata"].get("version")

    @property
    def src_url(self) -> str:
        src_url = self["build"].get("src_url", "")
        if not src_url:
            return ""

        if "{" in src_url and self.version:
            src_url = src_url.format(version=self.version)

        return src_url

    @property
    def src_git(self) -> str:
        return self["build"].get("src_git", "")


config = Config()


def build():
    sh("pip list")

    sh("mkdir src")

    if config.src_url:
        sh(f"curl -sL {config.src_url} | tar -xz -c src --strip-components 1 -f -")
    elif config.src_git:
        sh(f"git clone {config.src_git} src")
    else:
        raise Exception("Missing src_url or src_git")

    if is_python_project():
        build_python()


def is_python_project():
    if Path("src/requirements.txt").exists():
        return True
    elif Path("src/setup.py").exists():
        return True

    return False


def build_python():
    sh("python3 -m venv /nua/env")
    if Path("requirements.txt").exists():
        sh("/nua/env/bin/pip install -r src/requirements.txt")
    elif Path("setup.py").exists():
        sh("/nua/env/bin/pip install src")


def sh(cmd):
    print(cmd)
    sys.stdout.flush()
    status = os.system(cmd)
    if status != 0:
        print("Something whent wrong")
        sys.exit(status)


def main():
    fire.Fire(build)


if __name__ == "__main__":
    main()
