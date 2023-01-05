from os import chdir
from shutil import copy2

from nua.lib.actions import (
    download_extract,
    install_build_packages,
    install_meta_packages,
    install_packages,
    npm_install,
)
from nua.lib.shell import sh
from nua.runtime.nua_config import NuaConfig


def main():
    chdir("/nua/build")
    config = NuaConfig(".")
    src_url = config.src_url

    install_meta_packages(config.meta_packages)
    install_packages(config.packages)

    with install_build_packages(config.build_packages):
        npm_install("node-gyp", force=True)
        hedge_src = download_extract(src_url, "/nua/build")
        chdir(hedge_src)
        cmd = "bin/setup"
        sh(cmd)
        # cmd = "yarn add node-fetch"
        # sh(cmd)
        cmd = "yarn cache clean; rm -fr /tmp/*"
        sh(cmd)

    copy2("/nua/build/nua/config.json", "/nua/build/hedgedoc/")
    copy2("/nua/build/nua/healthcheck.mjs", "/nua/build/hedgedoc/")


if __name__ == "__main__":
    main()
