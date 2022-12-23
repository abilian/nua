"""Make a docker image for frappe/bench."""
import os

from nua.lib.actions import (  # pip_install_glob,
    append_bashrc,
    install_nodejs_via_nvm,
    install_package_list,
    pip_install,
)
from nua.lib.shell import chown_r, sh

# from nua.runtime.nua_config import NuaConfig
# from pathlib import Path
# from nua.lib.shell import chmod_r, mkdir_p, rm_fr

BENCH_PKGS = """apt-utils build-essential git mariadb-client postgresql-client
    gettext-base wget libssl-dev fonts-cantarell xfonts-75dpi xfonts-base locales
    build-essential cron curl vim iputils-ping watch tree nano less
    software-properties-common bash-completion libpq-dev libffi-dev liblcms2-dev
    libldap2-dev libmariadb-dev libsasl2-dev libtiff5-dev libwebp-dev redis-tools
    rlwrap tk8.6-dev ssh-client net-tools make libbz2-dev libsqlite3-dev zlib1g-dev
    libreadline-dev llvm libncurses5-dev libncursesw5-dev xz-utils tk-dev liblzma-dev
    xvfb libfontconfig wkhtmltopdf
"""


def main():
    os.chdir("/nua/build")
    print(os.environ)

    install_package_list(BENCH_PKGS)

    install_nodejs_via_nvm("/nua")  # erpnext 13/node14 14/node16
    chown_r("/nua", "nua", "nua")

    cmd = (
        "sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen "
        "&& dpkg-reconfigure --frontend=noninteractive locales"
    )
    sh(cmd)

    # broken
    # WKHTMLTOPDF_VERSION = "0.12.6-1"
    # ARCH = "amd64"
    # filename = f"wkhtmltox_{WKHTMLTOPDF_VERSION}.buster_{ARCH}.deb"
    # path = f"wkhtmltopdf/packaging/releases/download/{WKHTMLTOPDF_VERSION}/{filename}"
    # cmd = (
    #     f"wget -q https://github.com/{path} "
    #     f"&& dpkg -i {filename} "
    #     f"&& rm {filename}"
    # )
    # sh(cmd)

    # now use pypi:
    # repo = "https://github.com/frappe/bench.git"
    # branch = "develop"
    # cmd = f"git clone {repo} --depth 1 -b {develop} .bench && pip install -e .bench"
    # sh(cmd)

    bash = 'export PATH="/nua/venv/bin:/nua/.local/bin:$PATH"\nexport BENCH_DEVELOPER=1'
    append_bashrc("/nua", bash)

    pip_install("setuptools wheel", update=True)
    pip_install("frappe-bench==5.14.4")

    # pip_install(["setuptools", "wheel", "cryptography", "ansible~=2.8.15"])
    # install from a wheel
    # pip_install_glob("*.whl")

    # This app requires a maria DB. The DB is created by the start.py script at
    # start up if needed

    # create the base folder for html stuff
    # document_root = Path(config.build["document_root"] or "/var/www/html")
    # rm_fr(document_root)
    # mkdir_p(document_root)
    # chmod_r(document_root, 0o644, 0o755)


if __name__ == "__main__":
    main()
