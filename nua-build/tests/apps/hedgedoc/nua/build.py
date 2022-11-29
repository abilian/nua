from os import chdir
from shutil import copy2

from nua.lib.actions import (  # installed_packages,
    download_extract,
    install_package_list,
    install_psycopg2_python,
    npm_install,
    tmp_install_package_list,
)
from nua.lib.shell import sh


def main():
    release = "1.9.6"
    url = (
        "https://github.com/hedgedoc/hedgedoc/releases/"
        f"download/{release}/hedgedoc-{release}.tar.gz"
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
        hedge_src = download_extract(url, "/")
        chdir(hedge_src)
        cmd = "bin/setup"
        sh(cmd)
        cmd = "yarn cache clean; rm -fr /tmp/*"
        sh(cmd)

    install_package_list("netcat libsqlite3-dev")

    chdir("/nua")
    copy2("/nua/build/nua/config.json", "/hedgedoc/")


if __name__ == "__main__":
    main()
