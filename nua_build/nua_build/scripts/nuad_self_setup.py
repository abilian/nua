"""Script to install Nua dependancies on Nua app environment (inside docker).

command: "nua_build_self_setup"
"""

import os

from ..actions import install_package_list, pip_install
from ..rich_console import print_green
from ..shell import echo

# some packages may be alreay installed at Docker initial setup
# Python stuff needed for nua:
PACKAGES = [
    "apt-utils",
    "python3-dev",
]

PY_PACKAGES = []


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


def main() -> None:
    """Setup Nua base dependancies."""
    os.environ["DEBIAN_FRONTEND"] = "noninteractive"
    configure_apt()
    install_package_list(PACKAGES)
    pip_install(PY_PACKAGES)
    print_green("Nua: base components are installed.")
