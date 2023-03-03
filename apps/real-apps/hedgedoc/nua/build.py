from shutil import copy2

from nua.agent.nua_config import NuaConfig
from nua.lib.backports import chdir
from nua.lib.exec import exec_as_nua


def main():
    config = NuaConfig()
    src = config.fetch_source()

    with chdir(src):
        exec_as_nua(
            [
                "bin/setup",
                "yarn cache clean; rm -fr /tmp/*",
            ]
        )


if __name__ == "__main__":
    main()
