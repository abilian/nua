import os

from nua.lib.common.actions import install_package_list, poetry_install

# from nua.build.nua_config import NuaConfig

# from nua.lib.common.shell import mkdir_p, rm_fr, sh


def main():
    os.chdir("/nua/build")
    # config = NuaConfig(".")

    # this app requires some packages (for pg_config):
    install_package_list(["libpq-dev", "libpq5", "python3-dev", "gcc"])

    # poetry will grab the needed python packages (flask, gunicorn)
    poetry_install()

    # fix : replace psycopg2 by psycopg2-binary in requirements.txt
    # sh("pip install --no-cache-dir -r nua/requirements.txt")
    # sh("flask")

    # doc_root = Path(config.build["document_root"] or "/var/www/html")
    # rm_fr(doc_root)
    # mkdir_p(doc_root)
    # sh(f"chmod -R u=rwX,go=rX {doc_root}")


if __name__ == "__main__":
    main()
