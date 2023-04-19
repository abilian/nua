"""Bootstrap Nua orchestrator on the local host.

Use this script for installing the orchestrator on a new host.
- Create Nua account with admin rights,
- install base packages and configuration.

In future versions, change this to a standalone script.
"""
import multiprocessing as mp
import os
import platform
import shutil
import sys

# import venv -> this induces bugs (venv from venv...), prefer direct /usr/bin/python3
from pathlib import Path
from subprocess import run  # noqa: S404

from nua.lib.actions import (
    apt_final_clean,
    apt_update,
    check_python_version,
    install_package_list,
    string_in,
)
from nua.lib.console import print_blue, print_green, print_magenta
from nua.lib.exec import exec_as_nua, mp_exec_as_nua, set_nua_user
from nua.lib.panic import Abort, info
from nua.lib.shell import chown_r, mkdir_p, rm_fr, sh, user_exists

from .. import nua_env
from ..certbot.installer import install_certbot
from ..db_utils.mariadb_utils import bootstrap_install_mariadb, set_random_mariadb_pwd
from ..db_utils.postgres_utils import (
    bootstrap_install_postgres,
    set_random_postgres_pwd,
)
from ..nginx.installer import install_nginx

NUA = "nua"
HOST_PACKAGES = [
    "ca-certificates",
    "curl",
    "docker.io",
    "lsb-release",
    "git",
    "nginx-light",
    "software-properties-common",
    # "python3-certbot-nginx",
    # use pypi version of certbot, but still install the old ubuntu
    # version for /etc/letsencrypt/options-ssl-nginx.conf ?
]

PIP_PACKAGES = [
    "pip",
    "setuptools",
    "wheel",
    "poetry",
    "certbot",
    "certbot-nginx",
]


def main():
    print_blue("Installing Nua bootstrap script on local host...")

    if not check_python_version():
        raise Abort("Python 3.10+ is required for Nua installation.")

    if not platform.system() == "Linux":
        raise Abort("Nua currently only works on Linux.")

    if user_exists(NUA):
        info("Nua already installed. Proceeding anyway (overwwriting).")

    if os.geteuid() != 0:
        info("Not root, trying with sudo...")
        my_path = shutil.which("nua-bootstrap")
        run(["/usr/bin/sudo", str(my_path)], check=True)
        sys.exit(0)

    apt_update()
    bootstrap()
    apt_final_clean()

    print_green("\nNua installation done for user 'nua' on this host.")
    cmd = "nua-orchestrator --help"
    bash_as_nua(cmd)


def bootstrap():
    install_packages()
    create_nua_user()
    create_nua_venv()
    install_python_packages()
    bootstrap_install_postgres_or_fail()
    # bootstrap_install_mariadb_or_fail()
    install_nginx()
    install_certbot()
    install_local_orchestrator()
    # create_nua_key()
    # create_ssl_key()


def bootstrap_install_postgres_or_fail():
    if not bootstrap_install_postgres() or not set_random_postgres_pwd():
        raise Abort("Can't initialize Postgresql.")


def bootstrap_install_mariadb_or_fail():
    if not bootstrap_install_mariadb() or not set_random_mariadb_pwd():
        raise Abort("Can't initialize Mariadb.")


def install_packages():
    print_blue("Installing base packages...")
    install_package_list(HOST_PACKAGES, clean=False, keep_lists=True)


def create_nua_user():
    if not user_exists(NUA):
        print_blue("Creating user 'nua'...")
        cmd = "useradd --inactive -1 -G docker -m -s /bin/bash -U nua"
        # cmd = "useradd --inactive -1 -G sudo,docker -m -s /bin/bash -U nua"
        sh(cmd)

    record_nua_home()
    make_nua_dirs()
    nua_full_sudoer()


def nua_full_sudoer():
    print_blue("Modifying /etc/sudoers for user 'nua' (full access with no passwd)...")
    header = "# Nua: full access for Nua user:\n"
    # check already done:
    if string_in("/etc/sudoers", header):
        print_magenta("-> Prior changes found: do nothing")
        return

    with open("/etc/sudoers", "a") as sudofile:
        sudofile.write("\n")
        sudofile.write(header)
        sudofile.write("nua ALL=(ALL) NOPASSWD:ALL\n")


def record_nua_home():
    try:
        nua_env.detect_nua_home()
    except RuntimeError:
        raise Abort("Something weird append: can't find HOME of 'nua'")


def make_nua_dirs():
    home = nua_env.nua_home_path()
    for folder in (
        "tmp",
        "log",
        "db",
        "config",
        "apps",
        "images",
        "gits",
        "backups",
        "letsencrypt",
    ):
        mkdir_p(home / folder)
        chown_r(home / folder, NUA)
        os.chmod(home / folder, 0o755)  # noqa: S103


def create_nua_venv():
    print_blue("Creating the Python virtual environment for 'nua'")
    # assuming we already did check we have python >= 3.10
    host_python = "/usr/bin/python3"
    vname = "env"
    home = nua_env.nua_home_path()
    venv_path = home / vname
    nua_env.set_value("NUA_VENV", str(venv_path))
    if venv_path.is_dir():
        print_magenta(f"-> Prior {venv_path} found: do nothing")
    os.chdir(home)
    # venv.create(venv_path, with_pip=True)
    cmd = f"{host_python} -m venv {venv_path}"
    exec_as_nua(cmd, cwd="/home/nua")
    # chown_r(venv_path, NUA)
    header = "# Nua python virtual env:\n"
    if not string_in(".bashrc", header):
        with open(".bashrc", "a") as bashrc:
            bashrc.write("\n")
            bashrc.write(header)
            bashrc.write(f"source ~/{vname}/bin/activate\n")


def install_python_packages():
    print_blue("Installing local Python packages...")
    cmd = f"python -m pip install -U {' '.join(PIP_PACKAGES)}"
    bash_as_nua(cmd, "/home/nua")


def install_local_orchestrator():
    """WIP: maybe not the right thing to do: installation of orchestrator
    from git for nua user.
    """
    print_magenta("Installation of local Nua orchestrator (via git)")
    url = nua_env.get_value("NUA_GIT_URL")
    if not url:
        url = "https://github.com/abilian/nua.git"

    gits = nua_env.nua_home_path() / "gits"
    rm_fr(gits / "nua")

    cmd = f"git clone {url}"
    mp_exec_as_nua(cmd, gits)
    cmd = "git checkout main"
    mp_exec_as_nua(cmd, gits / "nua")
    pip_safe_install(gits / "nua")


def pip_safe_install(cwd: Path):
    pip = Path(nua_env.venv_bin()) / "pip"
    cmd = (
        f"{pip} list --format freeze | grep nua- | "
        f"xargs {pip} uninstall -qy 2> /dev/null"
    )
    bash_as_nua(cmd)
    cmd = "rm -fr ~/.cache"
    bash_as_nua(cmd)
    cmd = f"{pip} install --no-cache-dir ."
    bash_as_nua(cmd, cwd)


def bash_as_nua(cmd: str, cwd: str | Path | None = None, timeout: int | None = 600):
    env = nua_env.as_dict()
    if not cwd:
        cwd = nua_env.nua_home()
    if not timeout:
        timeout = 600
    proc = mp.Process(target=_bash_as_nua, args=(cmd, cwd, timeout, env))
    proc.start()
    proc.join()


def _bash_as_nua(cmd, cwd, timeout, env):
    set_nua_user()
    full_env = os.environ.copy()
    full_env.update(env)
    cmd = f"source {nua_env.get_value('NUA_VENV')}/bin/activate && {cmd}"
    run(
        cmd,
        shell=True,  # noqa: S602
        timeout=timeout,
        cwd=cwd,
        executable="/bin/bash",
        env=full_env,
    )


if __name__ == "__main__":
    main()
