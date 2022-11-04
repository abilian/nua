"""Bootstrap Nua config on the local host.

- Create Nua account with admin rights
- install base packages and configuration
"""
import os

# import venv -> this induce bugs (venv from venv...), prefer direct /usr/bin/python3
from pathlib import Path

from .. import nua_env
from ..actions import (
    apt_final_clean,
    apt_update,
    check_python_version,
    install_package_list,
    string_in,
)
from ..bash import bash_as_nua
from ..exec import exec_as_nua, mp_exec_as_nua
from ..mariadb_utils import bootstrap_install_mariadb, set_random_mariadb_pwd
from ..nginx_util import install_nginx
from ..panic import error, warning
from ..postgres_utils import bootstrap_install_postgres, set_random_postgres_pwd
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
    "software-properties-common",
    "python3-certbot-nginx",
]


def main():
    print_magenta("Installing Nua bootstrap on local host.")
    if not check_python_version():
        error("Python 3.10+ is required for Nua installation.")
    if user_exists(NUA):
        warning("Nua was already installed.")
    if os.geteuid() != 0:
        print_red(
            "Nua bootstrap script requires root privileges.\n"
            "Please try again, this time using 'sudo'.\n"
            "- When sudo, use absolute script path.\n"
            f"{detect_myself()}\n"
        )
        raise SystemExit(1)
    apt_update()
    bootstrap()
    apt_final_clean()
    print_green("\nNua installation done for user 'nua' on this host.")
    cmd = "nua --help"
    print(f"Command '{cmd}':")
    bash_as_nua("nua --help")


def detect_myself():
    venv = os.environ.get("VIRTUAL_ENV")
    if venv:
        return f"- Possible command:\n    sudo {Path(venv)/'bin'/'nua-bootstrap'}"
    else:
        return "- Current Python virtual env not detected."


def bootstrap():
    install_packages()
    create_nua_user()
    create_nua_venv()
    install_python_packages()
    bootstrap_install_postgres_or_fail()
    bootstrap_install_mariadb_or_fail()
    install_nginx()
    install_local_orchestrator()
    # create_nua_key()
    # create_ssl_key()


def bootstrap_install_postgres_or_fail():
    if not bootstrap_install_postgres() or not set_random_postgres_pwd():
        print_red("Nua bootstrap exiting.")
        raise SystemExit()


def bootstrap_install_mariadb_or_fail():
    if not bootstrap_install_mariadb() or not set_random_mariadb_pwd():
        print_red("Nua bootstrap exiting.")
        raise SystemExit()


def install_packages():
    print_magenta("Installation of base packages:")
    install_package_list(HOST_PACKAGES, update=False, clean=False, rm_lists=False)


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
    host_python = "/usr/bin/python3"
    vname = "nua310"
    home = nua_env.nua_home_path()
    venv_path = home / vname
    nua_env.set_value("NUA_VENV", str(venv_path))
    if venv_path.is_dir():
        print_red(f"-> Prior {venv_path} found: do nothing")
    os.chdir(home)
    # venv.create(venv_path, with_pip=True)
    cmd = f"{host_python} -m venv {venv_path}"
    exec_as_nua(cmd, cwd="/home/nua")
    # chown_r(venv_path, NUA)
    header = "# Nua python virtual env:\n"
    if not string_in(".bashrc", header):
        with open(".bashrc", "a") as bashrc:
            bashrc.write("\n")
            bashrc.write(header)
            bashrc.write(f"source ~/{vname}/bin/activate\n")


def install_python_packages():
    for package in ("pip", "setuptools", "wheel", "poetry"):
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
        url = "https://github.com/abilian/nua.git"
    gits = nua_env.nua_home_path() / "gits"
    os.chdir(gits)
    rm_fr(gits / "nua")
    cmd = f"git clone -o github {url}"
    mp_exec_as_nua(cmd)
    cwd = gits / "nua" / "nua_orchestrator"
    cmd = "./build.sh"
    bash_as_nua(cmd, cwd)
    cmd = "nua status"
    bash_as_nua(cmd)


if __name__ == "__main__":
    main()
