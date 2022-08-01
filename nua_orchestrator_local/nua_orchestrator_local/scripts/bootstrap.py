"""Bootstrap Nua config on the local host

- Create Nua account with admin rights
- install base packages and configuration
"""
import os
import sys
import venv
from pathlib import Path

from ..actions import check_python_version, install_package_list
from ..exec import exec_as_nua
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
        print_green("Nua already installed. Exiting.")
        sys.exit(0)
    if os.geteuid() != 0:
        print_red(
            "Nua bootstrap script requires root privileges.\n"
            "Please try again, this time using 'sudo'. Exiting."
        )
        sys.exit(1)
    bootstrap()


def bootstrap():
    install_packages()
    create_nua_user()
    create_nua_venv()
    # create_nua_key()
    # create_ssl_key()


def install_packages():
    print_magenta("Installation of base packages:")
    install_package_list(HOST_PACKAGES)


def create_nua_user():
    print_magenta("Creation of user 'nua'")
    cmd = "useradd --inactive -1 -G sudo,docker -m -s /bin/bash -U nua"
    sh(cmd)
    print_magenta("Modifying /etc/sudoers for user 'nua' (full access with no passwd)")
    with open("/etc/sudoers", "a") as sudofile:
        sudofile.write("\n")
        sudofile.write("# full access for Nua user:\n")
        sudofile.write("nua ALL=(ALL) NOPASSWD:ALL\n")


def create_nua_venv():
    print_magenta("Creation of Python virtual env for 'nua'")
    # assuming we already did check we have python >= 3.10
    vname = "nua310"
    home = Path("~nua").expanduser()
    os.chdir(home)
    venv.create(home / vname, with_pip=True)
    chown_r(home / vname, "nua", "nua")
    with open(".bashrc", "a") as bashrc:
        bashrc.write("# Nua python virtual env:\n")
        bashrc.write(f"source ~/{vname}/bin/activate\n")
    bin_py = home / vname / "bin" / "python"
    cmd = f"{bin_py} -m pip install -U pip"
    exec_as_nua(cmd)
    cmd = f"{bin_py} -m pip install -U setuptools"
    exec_as_nua(cmd)


if __name__ == "__main__":
    main()
