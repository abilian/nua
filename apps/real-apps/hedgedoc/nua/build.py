from os import chdir
from shutil import copy2

from nua.lib.actions import (
    download_extract,
    install_package_list,
    install_psycopg2_python,
    npm_install,
    tmp_install_package_list,
)
from nua.lib.shell import sh


def main():
    version = "1.9.6"
    src_url = (
        "https://github.com/hedgedoc/hedgedoc/releases/"
        f"download/{version}/hedgedoc-{version}.tar.gz"
    )
    packages = ["fontconfig", "fonts-noto"]
    tmp_packages = [
        "build-essential",
        "python3-dev",
        "libsqlite3-dev",
        "netcat",
        "libicu-dev",
        "libssl-dev",
        "git",
    ]

    install_psycopg2_python()

    install_package_list(packages, keep_lists=True)

    with tmp_install_package_list(tmp_packages):
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
