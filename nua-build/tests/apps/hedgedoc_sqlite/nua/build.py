from os import chdir

from nua.lib.actions import (  # installed_packages,
    download_extract,
    install_package_list,
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

    # print(installed_packages())
    # to test: can we remove {hedge_src}
    # cmd = f"yarn cache clean ; rm -fr /tmp/* ; rm -fr {hedge_src}"

    with tmp_install_package_list(tmp_packages):
        install_package_list(packages, rm_lists=False)
        npm_install("node-gyp", force=True)
        hedge_src = download_extract(url, "/nua/build")
        chdir(hedge_src)
        cmd = "bin/setup"
        sh(cmd)
        cmd = "yarn cache clean; rm -fr /tmp/*"
        sh(cmd)

    # print(installed_packages())


if __name__ == "__main__":
    main()
