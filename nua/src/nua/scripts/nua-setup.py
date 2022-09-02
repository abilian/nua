#!/bin/env python3

import os
import sys

os.environ["DEBIAN_FRONTEND"] = "noninteractive"

PACKAGES = [
    # Python stuff needed for nua
    "python3-pip",
    "python3-venv",
    "python3-toml",
    "python3-dev",
    "python3-wheel",
    # Stuff
    "apt-utils",
    # Web stuff
    "ca-certificates",
    "curl",
    # Build stuff
    "software-properties-common",
    "build-essential",
    "make",
    "gcc",
    "g++",
    "git",
    # DB stuff
    "libmysqlclient-dev",
]

PY_PACKAGES = [
    "fire",
    "rich",
]


def main():
    configure_apt()
    install_native_packages()
    install_python()
    install_nodejs()


def configure_apt():
    echo("Acquire::http {No-Cache=True;};", "/etc/apt/apt.conf.d/no-cache")
    echo(
        'APT::Install-Recommends "0"; APT::Install-Suggests "0";',
        "/etc/apt/apt.conf.d/01norecommend",
    )
    echo('Dir::Cache { srcpkgcache ""; pkgcache ""; }', "/etc/apt/apt.conf.d/02nocache")
    echo(
        'Acquire::GzipIndexes "true"; Acquire::CompressionTypes::Order:: "gz";',
        "/etc/apt/apt.conf.d/02compress-indexes",
    )


def install_native_packages():
    cmd = "apt-get update"
    sh(cmd)

    cmd = f"apt-get install -y {' '.join(PACKAGES)}"
    sh(cmd)


def install_python():
    cmd = f"python3 -m pip install {' '.join(PY_PACKAGES)}"
    sh(cmd)


def install_nodejs():
    cmd = "curl -sL https://deb.nodesource.com/setup_14.x | bash -"
    sh(cmd)

    sh("apt-get install -y nodejs")
    sh("/usr/bin/npm install -g yarn")


def echo(text: str, filename: str) -> None:
    with open(filename, "w") as fd:
        fd.write(text)


def sh(cmd):
    print(cmd)
    status = os.system(cmd)
    if status != 0:
        print("Something whent wrong")
        sys.exit(status)


main()
