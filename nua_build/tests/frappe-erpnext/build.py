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
            "build-essential",
            "curl",
            "git",
            "libffi-dev",
            "libfontconfig",
            "libmariadb-dev",
            "libmariadb3",
            "libmysqlclient-dev",
            "mariadb-client",
            "mariadb-server",
            "nodejs",
            "npm",
            "python3-dev",
            "python3-distutils",
            "python3-pip",
            "python3-setuptools",
            "python3.10-dev",
            "python3.10-venv",
            "redis-server",
            "software-properties-common",
            "wget",
            "wkhtmltopdf",
            "xvfb",
        ]
    )
    #
    #     sh(myql --user=root <<_EOF_
    # UPDATE mysql.user SET Password=PASSWORD('${db_root_password}') WHERE User='root';
    # DELETE FROM mysql.user WHERE User='';
    # DELETE FROM mysql.user WHERE User='root' AND Host NOT IN ('localhost', '127.0.0.1', '::1');
    # DROP DATABASE IF EXISTS test;
    # DELETE FROM mysql.db WHERE Db='test' OR Db='test\\_%';
    # FLUSH PRIVILEGES;
    # _EOF_)

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
