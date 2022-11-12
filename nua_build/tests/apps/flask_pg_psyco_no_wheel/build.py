import os
from pathlib import Path

from nua_build.common.actions import install_package_list, poetry_install
from nua_build.common.shell import chmod_r, mkdir_p, rm_fr
from nua_build.nua_config import NuaConfig


def main():
    os.chdir("/nua/build")
    config = NuaConfig(".")

    # this app requires some packages (for pg_config):
    install_package_list(["libpq-dev"])

    # poetry will grab the needed python packages from inside the container
    poetry_install()

    # This app requires a postges DB. The DB is created by the start.py script at
    # start up if needed

    # create the base folder for html stuff
    document_root = Path(config.build["document_root"] or "/var/www/html")
    rm_fr(document_root)
    mkdir_p(document_root)
    chmod_r(document_root, 0o644, 0o755)


if __name__ == "__main__":
    main()
