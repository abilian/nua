#!/bin/env python3
"""Script to build a nua package (experimental)

- informations come from a mandatory local file: "nua-config.toml"
- origin may be a source tar.gz or a git repository
- build locally if source is python package
"""
import errno
import logging
import os
import shutil
import sys
from pathlib import Path
from subprocess import call
from typing import Any

import fire
import rich.console
import toml

logging.basicConfig(level=logging.INFO)

console = rich.console.Console()


class Config:
    """Wrapper for the "nua-config.toml" file."""

    def __init__(self, path="nua-config.toml"):
        with open(path, encoding="utf8") as config_file:
            self._data = toml.load(config_file)

    def __getitem__(self, key: str) -> Any:
        """will return {} is key not found, assuming some parts are not
        mandatory and first level element are usually dict."""
        return self._data.get(key) or {}

    @property
    def metadata(self) -> dict:
        return self["metadata"]

    @property
    def version(self) -> str:
        """version of package source."""
        return self.metadata.get("version", "")

    @property
    def build(self) -> dict:
        return self["build"]

    @property
    def src_url(self) -> str:
        src_url = self.build.get("src_url") or ""
        if "{" in src_url and self.version:
            src_url = src_url.format(version=self.version)

        return src_url

    @property
    def src_git(self) -> str:
        return self.build.get("src_git") or ""


config = Config()


#### utils:


def is_python_project():
    if Path("src/requirements.txt").exists():
        return True
    if Path("src/setup.py").exists():
        return True

    return False


# Copied from from boltons.fileutils
def mkdir_p(path):
    """Creates a directory and any parent directories that may need to be
    created along the way, without raising errors for any existing directories.

    This function mimics the behavior of the ``mkdir -p`` command
    available in Linux/BSD environments, but also works on Windows.
    """
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            return
        raise
    return


def rm_rf(path: str):
    if Path(path).exists():
        shutil.rmtree(path)


def panic(msg: str, status: int = 1):
    console.print(msg, style="bold red")
    sys.exit(status)


def sh(cmd: str):
    console.print(cmd, style="green")
    try:
        status = call(cmd, shell=True)
        if status < 0:
            panic(f"Child was terminated by signal {-status}", status)
        elif status > 0:
            panic("Something went wrong", status)
    except OSError as e:
        panic(f"Execution failed: {e}")


#############################################################


def build_python():
    sh("python3 -m venv /nua/env")
    if Path("requirements.txt").exists():
        sh("/nua/env/bin/pip install -r src/requirements.txt")
    elif Path("setup.py").exists():
        sh("/nua/env/bin/pip install src")


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


def main():
    fire.Fire(build)


if __name__ == "__main__":
    main()
