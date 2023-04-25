import os
from pathlib import Path
from urllib.request import urlopen

from ..shell import sh
from .apt import apt_remove_lists, install_package_list, purge_package_list
from .util import append_bashrc


def npm_install(package: str, force: bool = False) -> None:
    """Install a node package globally."""
    opt = " --force" if force else ""
    cmd = f"/usr/bin/npm install -g{opt} {package}"
    sh(cmd)


def install_nodejs(version: str = "16.x", keep_lists: bool = False):
    """Install nodejs."""
    purge_package_list("yarn npm nodejs")
    url = f"https://deb.nodesource.com/setup_{version}"
    target = Path("/nua") / "install_node.sh"
    with urlopen(url) as remote:  # noqa S310
        target.write_bytes(remote.read())
    for cmd in (
        "bash /nua/install_node.sh",
        "apt-get install -y nodejs",
        "/usr/bin/npm update -g npm",
        "/usr/bin/npm install -g --force yarn",
        "/usr/bin/npm install -g --force node-gyp",
    ):
        sh(cmd)
    if not keep_lists:
        apt_remove_lists()


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
