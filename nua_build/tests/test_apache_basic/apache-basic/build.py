import os
from pathlib import Path
from shutil import copy2, copytree

from nua_build import __version__ as nua_version
from nua_build.nua_config import NuaConfig
from nua_build.scripting import *


def main():
    os.chdir("/nua/build")
    config = NuaConfig(".")

    packages = ["apache2"]
    install_package_list(packages)
    # sh("systemctl disable apache2")

    doc_root = Path(config.build["document_root"] or "/var/www/html")
    rm_fr(doc_root)
    mkdir_p(doc_root.parent)
    replace_in("html/*.html", "___nua_version___", nua_version)
    copytree("html", doc_root)
    chown_r(doc_root, "www-data", "www-data")
    sh(f"chmod -R u=rwX,go=rX {str(doc_root)}")

    sh("a2dissite 000-default.conf")
    replace_in("basic.conf", "___doc_root___", str(doc_root))
    copy2("basic.conf", "/etc/apache2/sites-available")
    sh("a2ensite basic.conf")


main()
