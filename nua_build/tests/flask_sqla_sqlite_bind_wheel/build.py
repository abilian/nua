import os
from pathlib import Path

from nua_build.actions import install_package_list, pip_install_glob
from nua_build.nua_config import NuaConfig
from nua_build.shell import chmod_r, mkdir_p, rm_fr, sh


def main():
    os.chdir("/nua/build")
    config = NuaConfig(".")

    # install from a wheel
    pip_install_glob("*.whl")


if __name__ == "__main__":
    main()
