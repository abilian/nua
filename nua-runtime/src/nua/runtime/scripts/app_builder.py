"""Install the configured application inside the container.

- information come from a mandatory local file: "nua-config.toml|json|yaml|yml"
- origin may be a source tar.gz or a git repository, python wheel
- build locally if source is python package
"""
import logging
import os
from pathlib import Path
from shutil import copy2

from nua.lib.actions import (
    apt_remove_lists,
    copy_from_package,
    install_build_packages,
    install_meta_packages,
    install_packages,
    install_pip_packages,
    project_install,
)
from nua.lib.backports import chdir
from nua.lib.panic import abort, info, show, warning
from nua.lib.shell import chmod_r, mkdir_p, rm_fr, sh
from nua.lib.tool.state import set_verbosity, verbosity, verbosity_level

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
        if "nua_verbosity" in os.environ:
            set_verbosity(int(os.environ["nua_verbosity"]))
            if verbosity():
                info("verbosity:", verbosity_level())
        self.build_dir = Path(NUA_BUILD_PATH)
        if not self.build_dir.is_dir():
            abort(f"Build directory does not exist: '{self.build_dir}'")
        chdir(self.build_dir)
        self.config = NuaConfig(self.build_dir)

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
        # Provided path must exist (or should have failed earlier)
        self.nua_dir = self.build_dir / nua_dir

    def build(self):
        self.detect_nua_dir()
        self.make_dirs()
        with chdir(self.config.root_dir):
            self.pre_build()
            self.detect_and_run_build()
            self.post_build()
        self.test_build()

    def pre_build(self):
        """Process installation of packages prior to unning install script."""
        install_meta_packages(self.config.meta_packages, keep_lists=True)
        install_packages(self.config.packages, keep_lists=True)
        install_pip_packages(self.config.pip_install)

    def make_dirs(self):
        mkdir_p(NUA_APP_PATH)
        mkdir_p(NUA_METADATA_PATH)
        self.make_custom_document_root()

    def make_custom_document_root(self):
        """If the app defines a specific document root  (i.e. /var/www/html)."""
        document_root = self.config.build.get(
            "document-root", self.config.build.get("document_root")
        )
        if not document_root:
            return
        path = Path(document_root)
        rm_fr(path)
        mkdir_p(path)
        chmod_r(path, 0o644, 0o755)

    def post_build(self):
        apt_remove_lists()
        self.copy_metadata()
        self.make_start_script()

    def test_build(self):
        """Execute a configured shell command to check build is successful."""
        command = self.config.build.get("test-cmd", self.config.build.get("test_cmd"))
        if not command:
            return
        show("build test command:", command)
        sh(command, show_cmd=False)

    def copy_metadata(self):
        """Dump the content of the nua-config file in /nua/metadata/nua-
        config.json."""
        self.config.dump_json(NUA_METADATA_PATH)

    def make_start_script(self):
        script_dir = Path(NUA_SCRIPTS_PATH)
        script_dir.mkdir(mode=0o755, parents=True, exist_ok=True)
        start_script = self.config.build.get("start_script", "start.py")
        if not start_script:
            start_script = "start.py"
        orig = self.nua_dir / start_script
        if orig.is_file():
            copy2(orig, script_dir)
        else:
            copy_from_package("nua.runtime.defaults", "start.py", script_dir)

    def find_build_script(self) -> Path | None:
        build_script = self.config.build.get("build_script", "build.py")
        if not build_script:
            build_script = "build.py"
        script_path = self.nua_dir / build_script
        script_path = script_path.absolute().resolve()
        if script_path.is_file():
            info(f"run build script: {script_path}")
            return script_path
        else:
            show("No build script found")
            return None

    def run_build_script(self):
        """Process the 'build.py' script if exists.

        The script is run from the directory of the nua-config.toml file.
        """
        script_path = self.find_build_script()
        if not script_path:
            return
        # assuming it is a python script
        with install_build_packages(self.config.build_packages):
            env = dict(os.environ)
            cmd = "python --version"
            sh(cmd, env=env)

            cmd = f"python {script_path}"
            sh(cmd, env=env, timeout=1800)

    def detect_and_run_build(self):
        """Detect the build method and apply.
        (WIP)

        Current guess:
            - "build.py"
            - "project" directory
        """
        if self.find_build_script():
            return self.run_build_script()
        elif self.config.project:
            return project_install(self.config.project)
        warning("No build method found")


def main() -> None:
    """Setup app in Nua container."""
    builder = BuilderApp()
    builder.fetch()
    builder.build()
