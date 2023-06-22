"""Nua scripting: action commands."""
import importlib.util
import os
import re
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path

from ..panic import Abort, show, warning
from ..shell import chown_r, sh
from ..tool.state import verbosity
from .apt import (
    _install_packages,
    apt_remove_lists,
    install_package_list,
    purge_package_list,
)
from .util import _glob_extended


#
# Builder for Python projects
#
def build_python(path: str | Path = "", user: str = ""):
    """Build a python project from source."""

    root = Path(path).expanduser().resolve()
    requirements = root / "requirements.txt"
    pyproject = root / "pyproject.toml"
    setup_py = root / "setup.py"
    if user:
        prefix = f"sudo -nu {user} "
    else:
        prefix = ""
    if requirements.is_file():
        sh(f"{prefix}python -m pip install -v -r {requirements} .", cwd=root)
    elif setup_py.is_file() or pyproject.is_file():
        sh(f"{prefix}python -m pip install -v .", cwd=root)
    else:
        warning(f"No method found to build the python project in '{root}'")


def install_python(version: str = "3.10", venv: str = "", keep_lists: bool = False):
    """Install a Python version and create a virtual environment."""

    PY_UBUNTU = {"2.7", "3.10"}
    PY_DEADSNAKES = {"3.7", "3.8", "3.9", "3.11"}
    if version not in PY_UBUNTU and version not in PY_DEADSNAKES:
        raise Abort(f"Unknown Python version: '{version}'")

    if not venv:
        venv = f"/nua/p{version.replace('.','')}"
    if version in PY_DEADSNAKES:
        sh("add-apt-repository -y ppa:deadsnakes/ppa")
    _install_python_packages(version)
    _make_python_venv(version, venv)
    chown_r(venv, "nua")
    if not keep_lists:
        apt_remove_lists()


def _install_python_packages(version: str):
    py = f"python{version}"
    if version == "2.7":
        packages = [
            "software-properties-common",
            py,
            f"{py}-dev",
            "virtualenv",
            "python-pip",
            f"{py}-distutils",
        ]
    else:
        packages = [
            "software-properties-common",
            py,
            f"{py}-dev",
            f"{py}-venv",
            f"{py}-distutils",
        ]
    _install_packages(packages)


def _venv_environ(venv: str) -> dict[str, str]:
    env = os.environ.copy()
    env["VIRTUAL_ENV"] = venv
    env["PATH"] = f"{venv}/bin:{env['PATH']}"
    return env


def _make_python_venv(version: str, venv: str):
    if version == "2.7":
        return _make_python_venv_27(venv)
    py = f"python{version}"
    sh(f"{py} -m venv {venv}")
    with python_venv(venv):
        sh("python -m pip install --upgrade setuptools wheel pip")


def _make_python_venv_27(venv: str):
    sh(f"virtualenv -p /usr/bin/python2.7 {venv}")
    with python_venv(venv):
        sh("pip2 install -U setuptools wheel pip")


@contextmanager
def python_venv(venv: str):
    """Activate a Python virtual environment."""
    orig_env = dict(os.environ)
    os.environ["VIRTUAL_ENV"] = venv
    os.environ["PATH"] = f"{venv}/bin:{orig_env['PATH']}"
    with verbosity(2):
        print(f"Using Python venv: '{venv}'")

    try:
        yield
    finally:
        os.environ.clear()
        os.environ.update(orig_env)


def install_pip_packages(packages: list | str | None = None) -> bool:
    if not packages:
        return False
    if isinstance(packages, str):
        packages = packages.strip().split()
    show("Installing pip packages declared in nua-config")
    return pip_install(_glob_extended(packages))


def pip_install(
    packages: list | str,
    update: bool = False,
    user: str = "",
) -> bool:
    if isinstance(packages, str):
        packages = packages.strip().split()
    if not packages:
        warning("pip_install(): nothing to install")
        return False
    option = "-U " if update else " "
    if user:
        prefix = f"sudo -nu {user} "
    else:
        prefix = ""
    cmd = f"{prefix}python -m pip install {option}{' '.join(packages)}"
    sh(cmd)
    return True


def pip_install_glob(pattern: str) -> None:
    packages = [str(f) for f in Path.cwd().glob(pattern)]
    if not packages:
        warning("pip_install_glob(): nothing to install")
        return
    cmd = f"python -m pip install {' '.join(packages)}"
    sh(cmd)


def pip_list():
    sh("pip list")


def poetry_install(nodev: bool = True) -> None:
    pip_install("poetry pip-autoremove")
    if nodev:
        sh("poetry install --only main")
    else:
        sh("poetry install")
    cmd = "pip-autoremove -y poetry"
    sh(cmd)


def install_mariadb_python(version: str = "1.1.4"):
    """Connector for MariaDB."""
    install_package_list(
        [
            "python3-dev",
            "libmariadb3",
            "libmariadb-dev",
            "mariadb-client",
            "unzip",
            "build-essential",
        ],
        keep_lists=True,
    )
    with tempfile.TemporaryDirectory(dir="/var/tmp") as tmpdirname:  # noqa S108
        cmd = f"python -m pip download mariadb=={version}"
        result = sh(cmd, cwd=tmpdirname, capture_output=True)
        saved_file = re.search("Saved(.*)\n", result).group(1).strip()  # type: ignore
        archive = Path(saved_file).name
        stem = Path(archive).stem
        if stem.endswith(".tar"):
            stem = Path(stem).stem
        if archive.endswith("zip"):
            unzip = f"unzip {archive}"  # for 1.1.4
        else:
            unzip = f"tar xzf {archive}"  # for 1.1.5.post2
        cmd = (
            f"{unzip} "
            f"&& cd {stem} && python setup.py bdist_wheel && mv dist/*.whl .."
        )
        sh(cmd, cwd=tmpdirname)
        pip_install_glob(f"tmpdirname/{stem}*.whl")

    purge_package_list("build-essential unzip")


def check_python_version() -> bool:
    """Check that curent python is >=3.10."""
    return sys.version_info >= (3, 10)


def python_package_installed(pkg_name: str) -> bool:
    """Utility to test if a python package is installed.

    Nota: replaced by some function using importlib.
    """
    return bool(importlib.util.find_spec(pkg_name))
