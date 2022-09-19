import os
from pathlib import Path

from nua_build.actions import install_package_list
from nua_build.nua_config import NuaConfig
from nua_build.shell import chmod_r, mkdir_p, rm_fr, sh


def main():
    os.chdir("/nua/build")
    config = NuaConfig(".")

    # this app requires some packages (for pg_config):
    install_package_list(["libpq-dev"])

    # poetry will grab the needed python packages (flask, gunicorn)
    sh("poetry install")

    # create the base folder for html stuff
    document_root = Path(config.build["document_root"] or "/var/www/html")
    rm_fr(document_root)
    mkdir_p(document_root)
    chmod_r(document_root, 0o644, 0o755)


if __name__ == "__main__":
    main()
