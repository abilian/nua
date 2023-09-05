import os
from pathlib import Path

from ..shell import sh
from .apt import (
    apt_remove_lists,
    install_build_packages,
    install_package_list,
    purge_package_list,
)
from .util import append_bashrc


def npm_install(package: str, force: bool = False) -> None:
    """Install a node package globally."""
    opt = " --force" if force else ""
    cmd = f"/usr/bin/npm install -g{opt} {package}"
    sh(cmd)


# deprecated since sept 2023
# def install_nodejs_old(version: str = "16.x", keep_lists: bool = False):
#     """Install nodejs."""
#     purge_package_list("yarn npm nodejs")
#     url = f"https://deb.nodesource.com/setup_{version}"
#     target = Path("/nua") / "install_node.sh"
#     download_url(url, target)
#     for cmd in (
#         "bash /nua/install_node.sh",
#         "apt-get install -y nodejs",
#         "/usr/bin/npm update -g npm",
#         "/usr/bin/npm install -g --force yarn",
#         "/usr/bin/npm install -g --force node-gyp",
#     ):
#         sh(cmd)
#     if not keep_lists:
#         apt_remove_lists()


def install_nodejs(version: str = "16", keep_lists: bool = False):
    """Install nodejs.

    from: https://nodesource.com/
    """
    _check_supported_nodejs_version(version)
    purge_package_list("yarn npm nodejs")
    fetch_cmd = (
        "/usr/bin/curl -fsSL "
        "https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | "
        "/usr/bin/gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg"
    )
    install_cmd = (
        'echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] '
        f'https://deb.nodesource.com/node_{version}.x nodistro main" | '
        "/usr/bin/tee /etc/apt/sources.list.d/nodesource.list"
    )
    with install_build_packages("curl gnupg", keep_lists=True):
        for cmd in (
            "mkdir -p /etc/apt/keyrings",
            fetch_cmd,
            install_cmd,
            "apt-get update",
            "apt-get install nodejs -y",
            "/usr/bin/npm install -g --force yarn",
            "/usr/bin/npm install -g --force node-gyp",
        ):
            sh(cmd)
    if not keep_lists:
        apt_remove_lists()


def _check_supported_nodejs_version(version: str) -> None:
    SUPPORTED = {"16", "18", "20"}
    if version not in SUPPORTED:
        raise RuntimeError(f"Unsupported NodeJs version {version}")


def install_nodejs_via_nvm(home: Path | str = "/nua"):
    """Install nodejs via nvm."""
    node_version_14 = "14.19.3"
    node_version = "16.18.0"
    # nvm_version = "v0.39.0"
    nvm_dir = f"{home}/.nvm"
    install_package_list("wget ", keep_lists=True)
    bashrc_modif = (
        f'export PATH="{nvm_dir}/versions/node/v{node_version}/bin/:$PATH"\n'
        f'export NVM_DIR="{nvm_dir}"\n'
        f'[ -s "$NVM_DIR/nvm.sh" ] && source "$NVM_DIR/nvm.sh"\n'
        f'[ -s "$NVM_DIR/bash_completion" ] && source "$NVM_DIR/bash_completion"'
    )
    append_bashrc(home, bashrc_modif)
    os.environ["NVM_DIR"] = ""
    os.environ["HOME"] = str(home)
    cmd = (
        f"wget -qO- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh "
        f"| bash  && . {nvm_dir}/nvm.sh "
        f"&& nvm install {node_version_14} "
        f"&& nvm use {node_version_14} "
        "&& npm install -g yarn "
        f"&& nvm install {node_version} "
        f"&& nvm use v{node_version} "
        "&& npm install -g yarn "
        f"&& nvm alias default v{node_version} "
        f"&& rm -rf {nvm_dir}/.cache "
    )
    environ = os.environ.copy()
    sh(cmd, env=environ)
