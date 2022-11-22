from os import chdir

from nua.lib.common.actions import (
    download_extract,
    install_nodejs,
    install_package_list,
    npm_install,
)
from nua.lib.common.shell import sh


def main():
    hedge_url = (
        "https://github.com/hedgedoc/hedgedoc/releases/"
        "download/1.9.6/hedgedoc-1.9.6.tar.gz"
    )
    install_nodejs(rm_lists=False)
    install_package_list(["git"], rm_lists=False, update=False)
    npm_install("node-gyp", force=True)
    hedge_path = download_extract(hedge_url, "/nua/build")
    chdir(hedge_path)
    cmd = "bin/setup"
    sh(cmd)


if __name__ == "__main__":
    main()
