"""Script to build Nua own images."""
import re
import tempfile
import zipfile
from pathlib import Path
from shutil import copy2
from urllib.request import urlopen

import tomli
import tomli_w
from nua.lib.backports import chdir
from nua.lib.panic import abort, vprint, warning
from nua.lib.shell import rm_fr, sh
from nua.lib.tool.state import verbosity

from .constants import CODE_URL


class NuaWheelBuilder:
    def __init__(self, wheel_path: Path, download: bool = False):
        self.wheel_path = wheel_path
        self.build_path = Path()
        self.download = download
        self.nua_local_git = None

    def make_wheels(self) -> bool:
        if self.download:
            return self._make_wheels_download()
        return self._make_wheels_local()

    def _make_wheels_download(self) -> bool:
        with verbosity(3):
            vprint("make_wheels(): download of source code forced")
        return self.build_from_download()

    def _make_wheels_local(self) -> bool:
        if self.check_devel_mode():
            with verbosity(3):
                vprint("make_wheels(): local git found")
            return self.build_from_local()
        with verbosity(3):
            vprint("make_wheels(): local git not found, will download")
        return self.build_from_download()

    @staticmethod
    def _nua_top() -> Path:
        return Path(__file__).resolve().parent.parent.parent.parent.parent

    @staticmethod
    def _quick_check(path: Path) -> bool:
        try:
            return all(
                (
                    (path / ".git").is_dir(),
                    (path / "nua-lib" / "pyproject.toml").is_file(),
                    (path / "nua-agent" / "pyproject.toml").is_file(),
                )
            )
        except (ValueError, OSError):
            return False

    def check_devel_mode(self) -> bool:
        """Try to find all required files locally in an up to date git repository.

        Warning: only for devel tests"""
        try:
            nua_top = self._nua_top()
            if self._quick_check(nua_top):
                self.nua_local_git = nua_top
                return True
            for path in (
                Path.home() / "gits" / "nua",
                Path.home() / "git" / "nua",
                Path.home() / "tmp" / "nua",
            ):
                if self._quick_check(path):
                    self.nua_local_git = path
                    return True
            return False
        except (ValueError, OSError):
            return False

    def build_from_download(self) -> bool:
        with tempfile.TemporaryDirectory() as build_dir:
            self.build_path = Path(build_dir)
            with verbosity(3):
                vprint(f"build_from_download() directory: {self.build_path}")
            target = self.build_path / "nua.zip"
            with verbosity(3):
                vprint(f"Dowloading '{CODE_URL}'")
            with urlopen(CODE_URL) as remote:  # noqa S310
                target.write_bytes(remote.read())
            with zipfile.ZipFile(target, "r") as zfile:
                zfile.extractall(self.build_path)
            return self.build_from(self.build_path / "nua-main")

    def build_from_local(self) -> bool:
        if not self.nua_local_git or not self.nua_local_git.is_dir():
            abort(f"Directory not found '{self.nua_local_git}'")
            return False  # for the qa
        with verbosity(3):
            vprint([f.name for f in self.nua_local_git.iterdir()])
        return all(
            (
                self.build_nua_lib(self.nua_local_git),
                self.build_nua_agent(self.nua_local_git),
            )
        )

    def build_nua_lib(self, top_git: Path) -> bool:
        return self.poetry_build(top_git / "nua-lib")

    def build_nua_agent(self, top_git: Path) -> bool:
        self.hack_agent_pyproject(top_git)
        return self.poetry_build(top_git / "nua-agent")

    @staticmethod
    def hack_agent_pyproject(top_git: Path):
        """Since we use local path dependencies when making wheel, we need to
        force the version deps to something local.

        FIXME: to be solved by publishing to Pypi index.
        """
        path = top_git / "nua-agent" / "pyproject.toml"
        pyproject = tomli.loads(path.read_text(encoding="utf8"))
        version = pyproject["tool"]["poetry"]["version"]
        dep = f"=={version}"
        pyproject["tool"]["poetry"]["dependencies"]["nua-lib"] = dep
        path.write_text(tomli_w.dumps(pyproject))

    def poetry_build(self, path: Path) -> bool:
        with verbosity(3):
            vprint(f"Poetry build in '{path}'")
        with chdir(path):
            rm_fr(path / "dist")
            cmd = "poetry build -f wheel"
            result = sh(cmd, capture_output=True, show_cmd=False)
            if not (done := re.search("- Built(.*)\n", result)):
                warning(f"Wheel not found for '{path}'")
                return False
            built = done.group(1).strip()
            wheel = path / "dist" / built
            copy2(wheel, self.wheel_path)
            with verbosity(2):
                vprint(f"Wheel copied: '{built}'")
            return True
