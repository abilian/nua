"""Script to build a nua package (experimental)

- informations come from a mandatory local file: "nua-config.toml"
- origin may be a source tar.gz or a git repository
- build locally if source is python package
"""
import logging
from os import chdir
from pathlib import Path
from shutil import copy2

from ..constants import (
    DEFAULTS_DIR,
    NUA_APP_PATH,
    NUA_BUILD_PATH,
    NUA_CONFIG,
    NUA_METADATA_PATH,
    NUA_SCRIPTS_PATH,
)
from ..nua_config import NuaConfig
from ..panic import error
from ..shell import mkdir_p, sh

logging.basicConfig(level=logging.INFO)


class BuilderApp:
    """Class to hold config and other state information during build."""

    def __init__(self):
        # we are supposed to launch "nua buld" from cwd, but we'll see later
        # self.root_dir = Path.cwd()
        self.build_dir = Path(NUA_BUILD_PATH)
        if not self.build_dir.is_dir():
            error(f"Build directory does not exist: '{self.build_dir}'")
        chdir(self.build_dir)
        self.config = NuaConfig(self.build_dir)
        self.build_script_path = None

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
            print("No src_url or src_git content to fetch.")

    def build(self):
        self.make_dirs()
        build_script = self.config.build.get("build_script") or "build.py"
        self.build_script_path = self.build_dir / build_script
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
        copy2(self.build_dir / NUA_CONFIG, Path(NUA_METADATA_PATH))

    def make_start_script(self):
        script_dir = Path(NUA_SCRIPTS_PATH)
        script_dir.mkdir(mode=0o755, parents=True, exist_ok=True)
        start_script = self.config.build.get("start_script") or "start.py"
        orig = self.build_dir / start_script
        if orig.is_file():
            copy2(orig, script_dir)
        else:
            copy2(DEFAULTS_DIR / "start.py", script_dir)

    def run_build_script(self):
        # assuming it is a python script
        print(f"run build script: {self.build_script_path}")
        chdir(self.build_dir)
        cmd = f"python {self.build_script_path}"
        sh(cmd, timeout=1800)


def main() -> None:
    """Setup app in Nua container."""
    builder = BuilderApp()
    builder.fetch()
    builder.build()
