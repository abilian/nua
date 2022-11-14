import os
from pathlib import Path
from shutil import copy2, copytree

from nua.lib.common.actions import install_package_list, replace_in
from nua.lib.common.shell import chmod_r, chown_r, mkdir_p, rm_fr, sh

from nua.build import __version__ as nua_version
from nua.build.nua_config import NuaConfig


def main():
    os.chdir("/nua/build")
    config = NuaConfig(".")

    packages = ["apache2"]
    install_package_list(packages)
    # sh("systemctl disable apache2")

    document_root = Path(config.build["document_root"] or "/var/www/html")
    rm_fr(document_root)
    mkdir_p(document_root.parent)
    replace_in("html/*.html", "___nua_version___", nua_version)
    copytree("html", document_root)
    chown_r(document_root, "www-data", "www-data")
    chmod_r(document_root, 0o644, 0o755)

    sh("a2dissite 000-default.conf")
    replace_in("basic.conf", "___doc_root___", str(document_root))
    copy2("basic.conf", "/etc/apache2/sites-available")
    sh("a2ensite basic.conf")


main()
