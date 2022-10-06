import os

from nua_build.actions import pip_install_glob

# from nua_build.nua_config import NuaConfig


def main():
    os.chdir("/nua/build")
    # config = NuaConfig(".")

    # install from a wheel
    pip_install_glob("*.whl")


if __name__ == "__main__":
    main()
