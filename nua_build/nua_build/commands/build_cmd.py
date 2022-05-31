#!/bin/env python3
"""Script to build a nua package (experimental)

- informations come from a mandatory local file: "nua-config.toml"
- origin may be a source tar.gz or a git repository
- build locally if source is python package

Note: **currently use "nuad ..." for command line**. See later if move this
to "nua ...".
"""

import logging
from pathlib import Path

import typer

from .nua_config import NuaConfig
from .scripting import is_python_project, sh

logging.basicConfig(level=logging.INFO)

app = typer.Typer()


def build_python():
    sh("python3 -m venv /nua/env")
    if Path("requirements.txt").exists():
        sh("/nua/env/bin/pip install -r src/requirements.txt")
    elif Path("setup.py").exists():
        sh("/nua/env/bin/pip install src")


@app.command("build")
def build_cmd() -> None:
    """Build package, using local 'nua-config.toml' file."""

    config = NuaConfig()

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
