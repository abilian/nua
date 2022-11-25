"""
require:
    libmariadb3 libmariadb-dev
"""
import os
from pathlib import Path

from nua.lib.actions import install_mariadb_1_1_5
from nua.lib.shell import chmod_r, mkdir_p, rm_fr
from nua.runtime.nua_config import NuaConfig


def main():
    os.chdir("/nua/build")
    config = NuaConfig(".")

    install_mariadb_1_1_5()

    # create the base folder for html stuff
    document_root = Path(config.build["document_root"] or "/var/www/html")
    rm_fr(document_root)
    mkdir_p(document_root)
    chmod_r(document_root, 0o644, 0o755)


if __name__ == "__main__":
    main()
