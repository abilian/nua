import os
from collections.abc import Iterable
from contextlib import contextmanager

from ..panic import show, warning
from ..shell import sh
from ..tool.state import packages_updated, set_packages_updated, verbosity
from .constants import LONG_TIMEOUT, SHORT_TIMEOUT


@contextmanager
def install_build_packages(
    packages: list | str,
    keep_lists: bool = False,
    installed: Iterable[str] | None = None,
):
    """Install packages needed for building a project."""
    success = True

    if installed:
        already = set(installed)
    else:
        already = set()

    if isinstance(packages, str):
        packages = packages.strip().split()

    needed = [package for package in packages if package not in already]
    if needed:
        with verbosity(2):
            show("Install temporary build packages")
        _install_packages(needed)

    try:
        yield
    except SystemExit:
        success = False
        raise
    finally:
        if success:
            if needed:
                with verbosity(2):
                    show("Remove temporary build packages")
                _purge_packages(needed)
            apt_final_clean()
            if not keep_lists:
                apt_remove_lists()


def apt_remove_lists():
    environ = os.environ.copy()
    sh("rm -rf /var/lib/apt/lists/*", env=environ, timeout=SHORT_TIMEOUT)
    set_packages_updated(False)


def apt_update():
    environ = os.environ.copy()
    environ["DEBIAN_FRONTEND"] = "noninteractive"
    cmd = "apt-get update --fix-missing"
    sh(cmd, env=environ, timeout=LONG_TIMEOUT, show_cmd=False)


def apt_final_clean():
    environ = os.environ.copy()
    environ["DEBIAN_FRONTEND"] = "noninteractive"
    cmd = "apt-get autoremove -y; apt-get clean"
    sh(cmd, env=environ, timeout=SHORT_TIMEOUT)


def _install_packages(packages: list):
    if not packages:
        warning("install_package(): nothing to install")
        return

    environ = os.environ.copy()
    environ["DEBIAN_FRONTEND"] = "noninteractive"
    if not packages_updated():
        cmd = "apt-get update --fix-missing; "
    else:
        cmd = ""
    cmd += f"apt-get install --no-install-recommends -y {' '.join(packages)}"
    sh(cmd, env=environ, timeout=LONG_TIMEOUT)
    set_packages_updated(True)


def _purge_packages(packages: list):
    if not packages:
        return

    print(f"Purge packages: {' '.join(packages)}")
    environ = os.environ.copy()
    environ["DEBIAN_FRONTEND"] = "noninteractive"
    for package in packages:
        cmd = f"apt-get purge -y {package} 2>/dev/null || true"
        sh(cmd, env=environ, timeout=SHORT_TIMEOUT, show_cmd=False)


def install_packages(packages: list, keep_lists: bool = False):
    if packages:
        with verbosity(2):
            show("install packages")
        install_package_list(packages, keep_lists=keep_lists)


def install_package_list(
    packages: list | str,
    clean: bool = True,
    keep_lists: bool = False,
):
    if isinstance(packages, str):
        packages = packages.strip().split()
    _install_packages(packages)
    if clean:
        apt_final_clean()
    if not keep_lists:
        apt_remove_lists()


def purge_package_list(packages: list | str):
    if isinstance(packages, str):
        packages = packages.strip().split()
    _purge_packages(packages)
    apt_final_clean()


@contextmanager
def tmp_install_package_list(
    packages: list | str,
    keep_lists: bool = True,
):
    if isinstance(packages, str):
        packages = packages.strip().split()
    _install_packages(packages)
    try:
        yield
    finally:
        _purge_packages(packages)
        apt_final_clean()
        if not keep_lists:
            apt_remove_lists()


def installed_packages() -> set[str]:
    cmd = "apt list --installed"
    result = sh(cmd, timeout=SHORT_TIMEOUT, capture_output=True, show_cmd=False)
    return {name.split("/")[0] for name in str(result).splitlines()}
