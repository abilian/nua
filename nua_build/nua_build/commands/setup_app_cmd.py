#!/bin/env python3
"""Script to build a nua package (experimental)

- informations come from a mandatory local file: "nua-config.toml"
- origin may be a source tar.gz or a git repository
- build locally if source is python package

Note: **currently use "nuad ..." for command line**. See later if move this
to "nua ...".
"""

import logging
from os import chdir
from pathlib import Path
from shutil import copy2, copytree, ignore_patterns

import typer

from ..nua_config import NuaConfig
from ..scripting import *

BUILD = "_build"
DEFAULTS_DIR = Path(__file__).parent.parent / "defaults"
MYSELF_DIR = Path(__file__).parent.parent.parent
assert DEFAULTS_DIR.is_dir()
assert MYSELF_DIR.is_dir()

logging.basicConfig(level=logging.INFO)

app = typer.Typer()


class BuilderApp:
    """Class to hold config and other state information during build."""

    def __init__(self, build_path: str):
        # we are supposed to launch "nua buld" from cwd, but we'll see later
        # self.root_dir = Path.cwd()
        if not build_path:
            build_path = "/nua/build"
        self.build_dir = Path(build_path)
        if not self.build_dir.is_dir():
            panic(f"Build directory does not exist: '{self.build_dir}'")
        chdir(self.build_dir)
        self.config = NuaConfig(folder=str(self.build_dir))

    def fetch(self):
        chdir(self.build_dir)
        if self.config.src_url:
            cmd = (
                f"curl -sL {self.config.src_url} | "
                "tar -xz -c src --strip-components 1 -f -"
            )
            sh(cmd)
        elif self.config.src_git:
            cmd = f"git clone {self.config.src_git} src"
            sh(cmd)
        else:
            panic("Missing src_url or src_git.")
        self.build_script_path = None

    def build(self):
        build_script = self.config.build.get("build_script", "")
        if build_script:
            self.build_script_path = self.build_dir / build_script
            # if not build_script_path.is_file():
            #     panic(f"Missing build_script: '{build_script_path}'")
        else:
            build_script_path = self.build_dir / "build.py"
            if build_script_path.is_file():
                # got the default build script
                self.build_script_path = build_script_path
        if self.build_script_path:
            self.run_build_script()
        else:
            print("here try to detect python package")

    def run_build_script(self):
        chdir(self.build_dir)
        cmd = f"python {self.build_script_path}"
        sh(cmd)


@app.command("setup_app")
def setup_app_cmd(build_path: str) -> None:
    """Setup app in Nua container."""

    builder = BuilderApp(build_path)
    builder.fetch()
    builder.build()
