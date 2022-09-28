import os
from pathlib import Path

from nua_build.actions import pip_install
from nua_build.nua_config import NuaConfig
from nua_build.shell import mkdir_p, rm_fr, sh


def main():
    os.chdir("/nua/build")
    config = NuaConfig(".")

    # poetry will grab the needed python packages (flask, gunicorn)
    pip_install("poetry")
    sh("poetry install")

    doc_root = Path(config.build["document_root"] or "/var/www/html")
    rm_fr(doc_root)
    mkdir_p(doc_root)
    sh(f"chmod -R u=rwX,go=rX {doc_root}")


if __name__ == "__main__":
    main()
