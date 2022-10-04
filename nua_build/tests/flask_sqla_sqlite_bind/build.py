import os
from pathlib import Path

from nua_build.actions import pip_install
from nua_build.nua_config import NuaConfig
from nua_build.shell import chmod_r, mkdir_p, rm_fr, sh


def main():
    os.chdir("/nua/build")
    config = NuaConfig(".")

    # poetry will grab the needed python packages (flask, gunicorn)
    pip_install("poetry")
    sh("poetry install")


if __name__ == "__main__":
    main()