import os

from nua_build.actions import pip_install_glob


def main():
    os.chdir("/nua/build")

    # install from a wheel
    pip_install_glob("*.whl")


if __name__ == "__main__":
    main()
