"""Install the configured application inside the container.

- information come from a mandatory local file: "nua-config.toml|json|yaml|yml"
- origin may be a source tar.gz or a git repository, python wheel
- build locally if source is python package
"""
import json
import logging
import os
from copy import deepcopy
from pathlib import Path
from pprint import pformat
from shutil import copy2

from nua.lib.actions import (
    apt_remove_lists,
    install_build_packages,
    install_git_source,
    install_meta_packages,
    install_packages,
    install_pip_packages,
    install_source,
    installed_packages,
)
from nua.lib.backports import chdir
from nua.lib.constants import (
    NUA_APP_PATH,
    NUA_BUILD_PATH,
    NUA_METADATA_PATH,
    NUA_SCRIPTS_PATH,
)
from nua.lib.exec import exec_as_nua, exec_as_root
from nua.lib.nua_config import NuaConfig, force_list, hyphen_get
from nua.lib.panic import Abort, info, show, vprint, warning
from nua.lib.shell import chmod_r, chown_r, mkdir_p, rm_fr, sh
from nua.lib.tool.state import (
    set_packages_updated,
    set_verbosity,
    verbosity,
    verbosity_level,
)

from ..auto_install import detect_and_install

logging.basicConfig(level=logging.INFO)


class AppBuilder:
    """Class to hold config and other state information during build."""

    def __init__(self):
        set_packages_updated(False)

        self.build_dir = Path(NUA_BUILD_PATH)
        if not self.build_dir.is_dir():
            raise Abort(f"Build directory does not exist: '{self.build_dir}'")

        chdir(self.build_dir)
        self.config = NuaConfig(self.build_dir)
        self.source = Path()

    def build(self):
        self.make_dirs()
        with chdir(self.config.root_dir):
            self.pre_build()
            with verbosity(1):
                info("******** Stage: build")
            with install_build_packages(
                self.config.build_packages,
                installed=installed_packages(),
            ):
                code_installed = self.install_project_code()
                chown_r("/nua/build", "nua")
                built = self.run_build_script(code_installed)
                if (code_installed or built) and os.getuid() == 0:
                    chown_r("/nua/build", "nua")

        self.post_build()
        self.test_build()
        with verbosity(1):
            show("******** Build done.")

    def collect_meta_packages(self) -> list[str]:
        """Return meta packages collected from the nua-config requirements
        and connectors required by providers."""
        collected_set = set()
        for provider in self.config.providers:
            collected_set.update(force_list(provider.get("connector") or ""))
        collected_set.update(force_list(self.config.meta_packages))
        return sorted(package for package in collected_set if package)

    def collect_packages(self) -> list[str]:
        """Return packages collected from the nua-config requirements."""
        collected_set = set()
        for provider in self.config.providers:
            collected_set.update(force_list(provider.get("packages", [])))
        collected_set.update(force_list(self.config.packages))
        return sorted(package for package in collected_set if package)

    def pre_build(self):
        """Process installation of packages prior to running install script."""
        with verbosity(1):
            info("******** Stage: pre-build")
        collection = self.collect_meta_packages()
        if collection:
            install_meta_packages(collection, keep_lists=True)
        collection = self.collect_packages()
        if collection:
            with verbosity(1):
                vprint(f"Install packages:  {collection}")
            install_packages(collection, keep_lists=True)
        chown_r("/nua/venv", "nua")

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
        with verbosity(1):
            info("******** Stage: post-build")
        self.merge_files()
        if os.getuid() == 0:
            chown_r("/nua/build", "nua")
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
        if self.config.start_command:
            with verbosity(2):
                vprint("Writing start script from 'start' content")
            return self._write_start_script(self.config.start_command)
        path = self.find_start_script()
        if path:
            with verbosity(2):
                vprint("Copying start script:", path)
            copy2(path, script_dir)
            return
        with verbosity(2):
            warning(
                "Neither start script or start-command found.\n"
                "Writing a debug start script showing container's environment."
            )
            return self._write_start_script(["env"])

    def _write_start_script(self, start_cmd: list):
        data = deepcopy(self.config.metadata_rendered)
        # data_str = json.dumps(data, indent=4)
        cwd = repr(str(self.source))
        cmd = f"""\
import os

from nua.lib.exec import exec_as_nua
from nua.agent.templates import render_config_templates

render_config_templates({pformat(data)})
exec_as_nua({start_cmd},
            cwd={cwd},
            env=os.environ,)
"""
        script_path = Path(NUA_SCRIPTS_PATH) / "start.py"
        script_path.write_text(cmd)
        with verbosity(2):
            vprint(cmd)

        # anticipate future change for start script:
        if self.is_requiring_templates():
            self._dump_template_data()
        else:
            self._write_shell_start_script(start_cmd)

    def is_requiring_templates(self) -> bool:
        templates_folder = Path("/nua/templates")

        if not templates_folder.is_dir():
            return False

        for file in templates_folder.rglob("*"):
            if not file.is_file():
                continue
            if file.name.startswith("."):
                continue
            return True

        return False

    def _dump_template_data(self):
        with verbosity(1):
            vprint("debug: this app is requiring templates")

        Path("/nua/metadata/template.json").write_text(
            json.dumps(
                self.config.metadata_rendered,
                ensure_ascii=False,
                indent=4,
                sort_keys=True,
            ),
            encoding="utf8",
        )

    def _write_shell_start_script(self, start_cmd: list):
        """Experimental, write a shell start command for dedicated dockerfile."""
        with verbosity(1):
            vprint("debug: write start.sh script")

        work_dir = repr(str(self.source.resolve()))
        # note: /bin/sh (dash on debian) does not support 'source', so using '.'
        cmd = [
            '# executed via "sh -c" as user nua',
            "[ -d /nua/venv ] && . /nua/venv/bin/activate",
            f"cd {work_dir}",
        ]
        cmd.extend(start_cmd)
        script_path = Path(NUA_SCRIPTS_PATH) / "start.sh"
        script_path.write_text("\n".join(cmd), encoding="utf8")
        chown_r(script_path, "nua")
        chmod_r(script_path, 0o755)  # noqa S103

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

    def run_build_script(self, code_installed: bool) -> bool:
        """Process the 'build.py' script if exists or the 'build' command.

        The script is run from the directory of the nua-config.toml file.
        """
        pip_installed = install_pip_packages(self.config.pip_install)

        if self.config.build_command:
            return self.build_with_command()

        if script_path := self.find_build_script():
            return self.build_with_script(script_path)

        return self.build_with_auto_detection(code_installed, pip_installed)

    def build_with_command(self) -> bool:
        """Process the 'build' commands.

        The script is run from the source directory.
        """
        with chdir(self.source):
            with verbosity(2):
                show("Execution of 'build' command")
            env = dict(os.environ)
            if self.config.build.get("build-as-root", False):
                exec_as_root(self.config.build_command, env=env, timeout=1800)
            else:
                exec_as_nua(self.config.build_command, env=env, timeout=1800)

        return True

    def build_with_script(self, script_path: Path) -> bool:
        """Build with a python script."""
        env = dict(os.environ)
        cmd = f"python {script_path}"
        if self.config.build.get("build-as-root", False):
            exec_as_root(cmd, env=env, timeout=1800)
        else:
            exec_as_nua(cmd, env=env, timeout=1800)

        return True

    def build_with_auto_detection(
        self,
        code_installed: bool,
        pip_installed: bool,
    ) -> bool:
        """Build with a auto detect/install.

        Rem: detect_and_install() is launched as root (the current user),
             it's the responsability of auto installer to switch to user nua.
        """
        if code_installed:
            return detect_and_install(self.source)

        if not any((pip_installed, code_installed)):
            # no package installed through install_pip_packages and
            # no other way. Let's assume there is a local project.
            show("Try install from some local project")
            return detect_and_install(".")

        return False

    def install_project_code(self) -> bool:
        if self.config.src_url:
            self.source = install_source(
                self.config.src_url,
                "/nua/build",
                self.config.app_id,
                self.config.src_checksum,
            )
            return True

        if self.config.project:
            self.source = install_source(
                self.config.project,
                "/nua/build",
                self.config.app_id,
            )
            return True

        if self.config.git_url:
            self.source = install_git_source(
                self.config.git_url, self.config.git_branch, "/nua/build"
            )
            return True

        return False

    def merge_files(self):
        """Copy content of various /nua/build/nua subfolders in /nua."""
        root = Path("/nua/build/nua")
        if not root.is_dir():
            with verbosity(3):
                print("not a directory: /nua/build/nua")
            return

        for item in root.iterdir():
            if item.name == "nua" or not item.is_dir():
                continue
            for file in item.glob("**/*"):
                if not file.is_file():
                    continue
                with verbosity(3):
                    print("merge file:", item)
                target = Path("/nua").joinpath(file.relative_to(root))
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
    if "nua_verbosity" in os.environ:
        set_verbosity(int(os.environ["nua_verbosity"]))
        with verbosity(3):
            info("verbosity:", verbosity_level())

    builder = AppBuilder()
    builder.build()
