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
    detect_and_install,
    install_build_packages,
    install_meta_packages,
    install_packages,
    install_pip_packages,
    install_source,
)
from nua.lib.backports import chdir
from nua.lib.exec import exec_as_nua
from nua.lib.panic import abort, info, show, vprint
from nua.lib.shell import chmod_r, chown_r, mkdir_p, rm_fr, sh
from nua.lib.tool.state import set_verbosity, verbosity, verbosity_level

from ..constants import (
    NUA_APP_PATH,
    NUA_BUILD_PATH,
    NUA_METADATA_PATH,
    NUA_SCRIPTS_PATH,
)

# most inferred meta packages will provided by plugins in the future:
from ..meta_packages import meta_packages_requirements
from ..nua_config import NuaConfig, hyphen_get

logging.basicConfig(level=logging.INFO)


class BuilderApp:
    """Class to hold config and other state information during build."""

    def __init__(self):
        # we are supposed to launch "nua buld" from cwd, but we'll see later
        # self.root_dir = Path.cwd()
        if "nua_verbosity" in os.environ:
            set_verbosity(int(os.environ["nua_verbosity"]))
            with verbosity(1):
                info("verbosity:", verbosity_level())
        self.build_dir = Path(NUA_BUILD_PATH)
        if not self.build_dir.is_dir():
            abort(f"Build directory does not exist: '{self.build_dir}'")
        chdir(self.build_dir)
        self.config = NuaConfig(self.build_dir)
        self.source = Path()

    def build(self):
        self.make_dirs()
        with chdir(self.config.root_dir):
            self.pre_build()
            code_installed = self.install_project_code()
            self.merge_files()
            if os.getuid() == 0:
                chown_r("/nua/build", "nua")
            pip_installed = install_pip_packages(self.config.pip_install)
            if code_installed:
                detect_and_install(self.source)
                if os.getuid() == 0:
                    chown_r("/nua/build", "nua")
            if not any((pip_installed, code_installed)):
                # no package installed through install_pip_packages and
                # no other way. Let's assume there is a local project.
                show("Try install from some local project")
                detect_and_install(".", self.config.name)
                if os.getuid() == 0:
                    chown_r("/nua/build", "nua")
            if code_installed:
                self.run_build_script()
        self.post_build()
        self.test_build()

    def infer_meta_packages(self) -> list:
        """Return packages inferred from the nua-config requirements."""
        inferred = []
        for resource in self.config.resource:
            inferred.extend(meta_packages_requirements(resource.get("type", "")))
        if inferred:
            with verbosity(2):
                vprint(f"Inferred meta packages: {inferred}")
        return inferred

    def pre_build(self):
        """Process installation of packages prior to running install script."""
        install_meta_packages(self.infer_meta_packages(), keep_lists=True)
        install_meta_packages(self.config.meta_packages, keep_lists=True)
        install_packages(self.config.packages, keep_lists=True)

    def make_dirs(self):
        self._make_dir_user_nua(NUA_APP_PATH)
        self._make_dir_user_nua(NUA_METADATA_PATH)
        self.make_custom_document_root()

    def make_custom_document_root(self):
        """If the app defines a specific document root  (i.e.
        /var/www/html)."""
        document_root = hyphen_get(self.config.build, "document-root")
        if not document_root:
            return
        path = Path(document_root)
        rm_fr(path)
        self._make_dir_user_nua(path)

    @staticmethod
    def _make_dir_user_nua(directory: str | Path):
        mkdir_p(directory)
        chown_r(directory, "nua")
        chmod_r(directory, 0o644, 0o755)

    def post_build(self):
        apt_remove_lists()
        self.copy_metadata()
        self.make_start_script()

    def copy_metadata(self):
        """Dump the content of the nua-config file in /nua/metadata/nua-
        config.json."""
        self.config.dump_json(NUA_METADATA_PATH)

    def make_start_script(self):
        script_dir = Path(NUA_SCRIPTS_PATH)
        script_dir.mkdir(mode=0o755, parents=True, exist_ok=True)
        path = self.find_start_script()
        if path:
            with verbosity(2):
                vprint("Copying start script:", path)
            copy2(path, script_dir)
        else:
            with verbosity(2):
                vprint("Copying default start script")
            copy_from_package("nua.agent.defaults", "start.py", script_dir)

    def find_start_script(self) -> Path | None:
        name = hyphen_get(self.config.build, "start-script")
        if not name:
            name = "start.py"
        path = self.build_dir / "nua" / name
        path = path.absolute().resolve()
        if path.is_file():
            with verbosity(3):
                vprint("found start_script path:", path)
            return path
        return None

    def find_build_script(self) -> Path | None:
        name = hyphen_get(self.config.build, "build-script")
        if not name:
            name = "build.py"
        path = self.build_dir / "nua" / name
        path = path.absolute().resolve()
        if path.is_file():
            with verbosity(3):
                info(f"found build script: {path}")
            return path
        return None

    def run_build_script(self):
        """Process the 'build.py' script if exists or the build-command.

        The script is run from the directory of the nua-config.toml
        file.
        """
        if self.config.build_command:
            return self.build_command()
        script_path = self.find_build_script()
        if not script_path:
            return
        # assuming it is a python script
        with install_build_packages(self.config.build_packages):
            env = dict(os.environ)
            with verbosity(2):
                cmd = "python --version"
                sh(cmd, env=env)
            cmd = f"python {script_path}"
            sh(cmd, env=env, timeout=1800)

    def build_command(self):
        """Process the 'build-command' commands.

        The script is run from the sources dirctory.
        """
        if not self.config.build_command:
            return
        # assuming it is a python script
        with install_build_packages(self.config.build_packages):
            with chdir(self.source):
                exec_as_nua(self.config.build_command)

    def install_project_code(self) -> bool:
        installed = False
        if self.config.src_url:
            self.source = install_source(
                self.config.src_url,
                "/nua/build",
                self.config.name,
                self.config.checksum,
            )
            installed = True

        elif self.config.project:
            self.source = install_source(
                self.config.project,
                "/nua/build",
                self.config.name,
            )
            installed = True
        elif self.config.git_url:
            pass
        return installed

    def merge_files(self):
        """Copy content of various /nua/build/nua subfolders in /nua"""
        root = Path("/nua/build/nua")
        if not root.is_dir():
            return
        for item in root.iterdir():
            if item.name == "nua" or not item.is_dir():
                continue
            for file in item.glob("**"):
                if not file.is_file():
                    continue
                target = Path("/nua/build").joinpath(file.relative_to(root))
                target.parent.mkdir(parents=True, exist_ok=True)
                copy2(file, target.parent)

    def test_build(self):
        """Execute a configured shell command to check build is successful."""
        default = "test -f /nua/metadata/nua-config.*"
        command = self.config.build.get("test", default)
        if not command:
            return
        show("Execution of build test command:", command)
        sh(command, show_cmd=False)


def main() -> None:
    """Setup app in Nua container."""
    builder = BuilderApp()
    builder.build()
