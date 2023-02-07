from shutil import copy2

from nua.agent.nua_config import NuaConfig
from nua.lib.actions import download_extract, npm_install
from nua.lib.backports import chdir
from nua.lib.shell import sh


def main():
    config = NuaConfig()
    src_url = config.src_url
    hedge_src = download_extract(src_url, "/nua/build")

    with chdir(hedge_src):
        cmd = "bin/setup"
        sh(cmd)
        cmd = "yarn cache clean; rm -fr /tmp/*"
        sh(cmd)

    copy2("nua/config.json", "/nua/build/hedgedoc/")
    copy2("nua/healthcheck.mjs", "/nua/build/hedgedoc/")


if __name__ == "__main__":
    main()
