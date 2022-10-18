"""

args options


os.environ['SUDO_USER']
Please run this script as a non-root user with sudo privileges, but without using sudo or pass --user=USER')
"""
import os
from pathlib import Path

from nua_build.actions import (
    install_nodejs,
    install_package_list,
    pip_install,
    pip_install_glob,
)
from nua_build.nua_config import NuaConfig
from nua_build.shell import chmod_r, mkdir_p, rm_fr, sh


def main():
    os.chdir("/nua/build")
    config = NuaConfig(".")

    # this app requires some packages (for mariadb_config):
    install_package_list(
        [
            "git",
            "redis-server",
            "build-essential",
            "python3-setuptools",
            "python3-dev",
            "libffi-dev",
            "software-properties-common",
            "curl",
            "wget",
            "libmariadb3",
            "libmariadb-dev",
            "mariadb-client",
            "xvfb",
            "libfontconfig",
            "wkhtmltopdf",
            "nodejs",
            "npm",
        ]
    )
    # install_nodejs("16.x")
    sh("npm install -g yarn")
    pip_install(["setuptools", "wheel", "cryptography", "ansible~=2.8.15"])
    # install from a wheel
    pip_install_glob("*.whl")
    pip_install("frappe-bench")

    # This app requires a maria DB. The DB is created by the start.py script at
    # start up if needed

    # create the base folder for html stuff
    # document_root = Path(config.build["document_root"] or "/var/www/html")
    # rm_fr(document_root)
    # mkdir_p(document_root)
    # chmod_r(document_root, 0o644, 0o755)


if __name__ == "__main__":
    main()
