"""Bootstrap Nua config on the local host.

- Create Nua account with admin rights
- install base packages and configuration
"""
import os
import sys
import venv

from .. import nua_env
from ..actions import check_python_version, install_package_list, string_in
from ..exec import mp_exec_as_nua
from ..nginx_util import install_nginx
from ..rich_console import print_green, print_magenta, print_red
from ..shell import chown_r, sh, user_exists

HOST_PACKAGES = [
    "ca-certificates",
    "curl",
    "docker.io",
    "lsb-release",
    "nginx-light",
    "postgresql-all",
    "software-properties-common",
]


def main():
    print_magenta("Installing Nua bootstrap on local host.")
    if not check_python_version():
        print_red("Python 3.10+ is required for Nua installation.")
        sys.exit(1)
    if user_exists("nua"):
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
    install_nginx()
    # create_nua_key()
    # create_ssl_key()


def install_packages():
    print_magenta("Installation of base packages:")
    install_package_list(HOST_PACKAGES)


def create_nua_user():
    if not user_exists("nua"):
        print_magenta("Creation of user 'nua'")
        cmd = "useradd --inactive -1 -G docker -m -s /bin/bash -U nua"
        # cmd = "useradd --inactive -1 -G sudo,docker -m -s /bin/bash -U nua"
        sh(cmd)
    record_nua_home()
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


def create_nua_venv():
    print_magenta("Creation of Python virtual environment for 'nua'")
    # assuming we already did check we have python >= 3.10
    vname = "nua310"
    home = nua_env.nua_home_path()
    venv_path = home / vname
    if venv_path.is_dir():
        print_red(f"-> Prior {venv_path} found: do nothing")
        return
    os.chdir(home)
    venv.create(venv_path, with_pip=True)
    chown_r(venv_path, "nua", "nua")
    header = "# Nua python virtual env:\n"
    if not string_in(".bashrc", header):
        with open(".bashrc", "a") as bashrc:
            bashrc.write(header)
            bashrc.write(f"source ~/{vname}/bin/activate\n")
    bin_py = venv_path / "bin" / "python"
    cmd = f"{bin_py} -m pip install -U pip"
    mp_exec_as_nua(cmd)
    cmd = f"{bin_py} -m pip install -U setuptools"
    mp_exec_as_nua(cmd)


if __name__ == "__main__":
    main()
