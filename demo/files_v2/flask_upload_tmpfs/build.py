import os
from pathlib import Path

from nua.lib.actions import pip_install_glob
from nua.lib.shell import chmod_r, mkdir_p, rm_fr
from nua.runtime.nua_config import NuaConfig

MOUNT_POINT = Path("/var/tmp/mount_point")


def main():
    os.chdir("/nua/build")
    config = NuaConfig(".")

    # install from a wheel
    pip_install_glob("*.whl")

    document_root = Path(config.build["document_root"] or "/var/www/html")
    rm_fr(document_root)
    mkdir_p(document_root)
    chmod_r(document_root, 0o644, 0o755)


if __name__ == "__main__":
    main()
