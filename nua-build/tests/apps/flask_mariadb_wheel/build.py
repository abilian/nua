"""
require:
    libmariadb3 libmariadb-dev
"""
import os
from pathlib import Path

from nua.lib.actions import install_mariadb_python, pip_install_glob
from nua.lib.shell import chmod_r, mkdir_p, rm_fr
from nua.runtime.nua_config import NuaConfig


def main():
    os.chdir("/nua/build")
    config = NuaConfig(".")

    # this app requires some packages (for mariadb_config):
    # install_package_list(["libmariadb3", "libmariadb-dev", "mariadb-client"])

    # This app requires a maria DB. The DB is created by the start.py script at
    # start up if needed
    install_mariadb_python()
    # install the app from its wheel
    pip_install_glob("*.whl")

    # create the base folder for html stuff
    document_root = Path(config.build["document_root"] or "/var/www/html")
    rm_fr(document_root)
    mkdir_p(document_root)
    chmod_r(document_root, 0o644, 0o755)


if __name__ == "__main__":
    main()
