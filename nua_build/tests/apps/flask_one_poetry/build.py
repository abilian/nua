import os
from pathlib import Path

from nua_build.common.actions import pip_install, poetry_install
from nua_build.nua_config import NuaConfig
from nua_build.shell import chmod_r, mkdir_p, rm_fr


def main():
    os.chdir("/nua/build")
    config = NuaConfig(".")

    pip_install("gunicorn")
    # poetry will grab the needed python packages from inside the container
    poetry_install()

    # create the base folder for html stuff
    document_root = Path(config.build["document_root"] or "/var/www/html")
    rm_fr(document_root)
    mkdir_p(document_root)
    chmod_r(document_root, 0o644, 0o755)


if __name__ == "__main__":
    main()
