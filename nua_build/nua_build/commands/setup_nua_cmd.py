#!/bin/env python3
"""Script to install Nua dependancies on Nua app environment (inside docker).

command: "nuad setup"

Note: **currently use "nuad ..." for command line**. See later if move this
to "nua ...".
"""

import os

import typer

from ..scripting import *

# some packages may be alreay installed at Docker initial setup
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
    "typer",
    "rich",
]

app = typer.Typer()


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
    cmd = "apt-get -y update"
    sh(cmd)
    apt_get_install(PACKAGES)


def install_nodejs():
    cmd = "curl -sL https://deb.nodesource.com/setup_14.x | bash -"
    sh(cmd)
    apt_get_install("nodejs")
    npm_install("yarn")


@app.command("setup_nua")
def setup_nua_cmd() -> None:
    """Setup Nua base dependancies."""
    os.environ["DEBIAN_FRONTEND"] = "noninteractive"
    configure_apt()
    install_native_packages()
    pip_install(PY_PACKAGES)
    print_green("Nua: base components are installed.")
