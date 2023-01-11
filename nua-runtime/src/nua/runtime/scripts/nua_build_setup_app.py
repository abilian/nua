"""Script to build a nua package (experimental)

- information come from a mandatory local file: "nua-config.toml|json|yaml|yml"
- origin may be a source tar.gz or a git repository
- build locally if source is python package
"""
import logging
import os
from os import chdir
from pathlib import Path
from shutil import copy2

from nua.lib.actions import copy_from_package
from nua.lib.panic import abort
from nua.lib.shell import mkdir_p, sh

from ..constants import (
    NUA_APP_PATH,
    NUA_BUILD_PATH,
    NUA_METADATA_PATH,
    NUA_SCRIPTS_PATH,
)
from ..nua_config import NuaConfig

logging.basicConfig(level=logging.INFO)


class BuilderApp:
    """Class to hold config and other state information during build."""

    nua_dir: Path

    def __init__(self):
        # we are supposed to launch "nua buld" from cwd, but we'll see later
        # self.root_dir = Path.cwd()
        self.build_dir = Path(NUA_BUILD_PATH)
        if not self.build_dir.is_dir():
            abort(f"Build directory does not exist: '{self.build_dir}'")
        chdir(self.build_dir)
        self.config = NuaConfig(self.build_dir)
        self.build_script_path = None
        # self.nua_dir = None

    def fetch(self):
        pass
        # chdir(self.build_dir)
        # if self.config.source_url:
        #     cmd = (
        #         f"curl -sL {self.config.source_url} | "
        #         "tar -xz -c src --strip-components 1 -f -"
        #     )
        #     sh(cmd)
        # elif self.config.src_git:
        #     cmd = f"git clone {self.config.src_git} src"
        #     sh(cmd)
        # else:
        #     print("No src_url or src_git content to fetch.")

    def detect_nua_dir(self):
        """Detect dir containing nua files (start.py, build.py, Dockerfile)."""
        nua_dir = self.config.build.get("nua_dir")
        if not nua_dir:
            # Check if default 'nua' dir exists
            path = self.build_dir / "nua"
            if path.is_dir():
                self.nua_dir = path
            else:
                # Use the root folder (where is the nua-config.toml file)
                self.nua_dir = self.build_dir
            return
        # Provided path must exists (or should have failed earlier)
        self.nua_dir = self.build_dir / nua_dir

    def build(self):
        self.detect_nua_dir()
        self.make_dirs()
        build_script = self.config.build.get("build_script") or "build.py"
        self.build_script_path = self.nua_dir / build_script
        if self.build_script_path.is_file():
            self.run_build_script()
        else:
            print(f"No build script. Not found: {self.build_script_path}")
        self.copy_metadata()
        self.make_start_script()

    def make_dirs(self):
        mkdir_p(NUA_APP_PATH)
        mkdir_p(NUA_METADATA_PATH)

    def copy_metadata(self):
        """Dump the content of the nua-config file in /nua/metadata/nua-config.json."""
        self.config.dump_json(NUA_METADATA_PATH)

    def make_start_script(self):
        script_dir = Path(NUA_SCRIPTS_PATH)
        script_dir.mkdir(mode=0o755, parents=True, exist_ok=True)
        start_script = self.config.build.get("start_script") or "start.py"
        orig = self.nua_dir / start_script
        if orig.is_file():
            copy2(orig, script_dir)
        else:
            copy_from_package("nua.runtime.defaults", "start.py", script_dir)

    def run_build_script(self):
        # assuming it is a python script
        print(f"run build script: {self.build_script_path}")
        chdir(self.build_dir)
        env = dict(os.environ)

        cmd = "python --version"
        sh(cmd, env=env)

        cmd = f"python {self.build_script_path}"
        sh(cmd, env=env, timeout=1800)


def main() -> None:
    """Setup app in Nua container."""
    builder = BuilderApp()
    builder.fetch()
    builder.build()
