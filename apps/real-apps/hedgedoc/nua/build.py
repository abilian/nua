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

    copy2("nua/config.json", "/nua/build/hedgedoc/")
    copy2("nua/healthcheck.mjs", "/nua/build/hedgedoc/")


if __name__ == "__main__":
    main()
