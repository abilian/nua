"""Bootstrap Nua config on the local host.

- Create Nua account with admin rights
- install base packages and configuration
"""
import os
import sys
import venv

from .. import nua_env
from ..actions import check_python_version, install_package_list, string_in
from ..bash import bash_as_nua
from ..exec import mp_exec_as_nua
from ..nginx_util import install_nginx
from ..rich_console import print_green, print_magenta, print_red
from ..shell import chown_r, mkdir_p, rm_fr, sh, user_exists

NUA = "nua"
HOST_PACKAGES = [
    "ca-certificates",
    "curl",
    "docker.io",
    "lsb-release",
    "git",
    "nginx-light",
    "postgresql-all",
    "software-properties-common",
]


def main():
    print_magenta("Installing Nua bootstrap on local host.")
    if not check_python_version():
        print_red("Python 3.10+ is required for Nua installation.")
        sys.exit(1)
    if user_exists(NUA):
        print_red("Warning: Nua was already installed.")
    if os.geteuid() != 0:
        print_red(
            "Nua bootstrap script requires root privileges.\n"
            "Please try again, this time using 'sudo'.\n"
            "(When sudo, use absolute script path).\n"
        )
        sys.exit(1)
    bootstrap()
    print_green("Nua installation done.")


def bootstrap():
    install_packages()
    create_nua_user()
    create_nua_venv()
    install_python_packages()
    install_nginx()
    install_local_orchestrator()
    # create_nua_key()
    # create_ssl_key()


def install_packages():
    print_magenta("Installation of base packages:")
    install_package_list(HOST_PACKAGES)


def create_nua_user():
    if not user_exists(NUA):
        print_magenta("Creation of user 'nua'")
        cmd = "useradd --inactive -1 -G docker -m -s /bin/bash -U nua"
        # cmd = "useradd --inactive -1 -G sudo,docker -m -s /bin/bash -U nua"
        sh(cmd)
    record_nua_home()
    make_nua_dirs()
    nua_full_sudoer()


def nua_full_sudoer():
    print_magenta("Modifying /etc/sudoers for user 'nua' (full access with no passwd)")
    header = "# Nua: full access for Nua user:\n"
    # check already done:
    if string_in("/etc/sudoers", header):
        print_magenta("-> Prior changes found: do nothing")
        return
    with open("/etc/sudoers", "a") as sudofile:
        sudofile.write("\n")
        sudofile.write(header)
        sudofile.write("nua ALL=(ALL) NOPASSWD:ALL\n")


def record_nua_home():
    try:
        nua_env.detect_nua_home()
    except RuntimeError:
        print_red("Something weird append: can't find HOME of 'nua'")
        raise


def make_nua_dirs():
    home = nua_env.nua_home_path()
    for folder in ("tmp", "log", "db", "config", "apps", "images", "gits", "backups"):
        mkdir_p(home / folder)
        chown_r(home / folder, NUA)
        os.chmod(home / folder, 0o755)  # noqa: S103


def create_nua_venv():
    print_magenta("Creation of Python virtual environment for 'nua'")
    # assuming we already did check we have python >= 3.10
    vname = "nua310"
    home = nua_env.nua_home_path()
    venv_path = home / vname
    nua_env.set_value("NUA_VENV", str(venv_path))
    if venv_path.is_dir():
        print_red(f"-> Prior {venv_path} found: do nothing")
    os.chdir(home)
    venv.create(venv_path, with_pip=True)
    chown_r(venv_path, NUA)
    header = "# Nua python virtual env:\n"
    if not string_in(".bashrc", header):
        with open(".bashrc", "a") as bashrc:
            bashrc.write("\n")
            bashrc.write(header)
            bashrc.write(f"source ~/{vname}/bin/activate\n")


def install_python_packages():
    for package in ("pip", "setuptools", "poetry"):
        print_magenta(f"Install {package}")
        cmd = f"python -m pip install -U {package}"
        bash_as_nua(cmd, "/home/nua")


def install_local_orchestrator():
    """WIP: maybe not the right thing to do: installation of orchestrator
    from git for nua user.
    """
    print_magenta("Installation of local Nua orchestrator (via git)")
    url = nua_env.get_value("NUA_GIT_URL")
    if not url:
        url = f"https://github.com/abilian/nua.git"
    gits = nua_env.nua_home_path() / "gits"
    os.chdir(gits)
    rm_fr(gits / "nua")
    cmd = f"git clone -o github {url}"
    mp_exec_as_nua(cmd)
    cwd = gits / "nua" / "nua_orchestrator_local"
    cmd = "./build_dev.sh"
    bash_as_nua(cmd, cwd)
    cmd = "nua-orchestrator-local status"
    bash_as_nua(cmd)


if __name__ == "__main__":
    main()
