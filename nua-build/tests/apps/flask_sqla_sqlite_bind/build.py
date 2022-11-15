from nua.lib.common.actions import poetry_install

# from nua.runtime.nua_config import NuaConfig


def main():
    # os.chdir("/nua/build")
    # config = NuaConfig(".")

    # poetry will grab the needed python packages (flask, gunicorn)
    poetry_install()


if __name__ == "__main__":
    main()
