"""Bootstrap Nua config on the local host

- Create Nua account with admin rights
- install base packages and configuration
"""
import os
import sys
import venv
from pathlib import Path
from shutil import copy2

from ..actions import (
    check_python_version,
    environ_replace_in,
    install_package_list,
    string_in,
)
from ..exec import exec_as_nua
from ..rich_console import print_green, print_magenta, print_red
from ..shell import chown_r, mkdir_p, sh, user_exists

# todo: find NUA_SERVERNAME somewhere
NUA_ENV = {"NUA_SERVERNAME": "exemple.com"}

HOST_PACKAGES = [
    "ca-certificates",
    "curl",
    "docker.io",
    "lsb-release",
    "nginx-light",
    "postgresql-all",
    "software-properties-common",
]


def main():
    print_magenta("Installing Nua bootstrap on local host.")
    if not check_python_version():
        print_red("Python 3.10+ is required for Nua installation.")
        sys.exit(1)
    if user_exists("nua"):
        print_red("Warning: Nua was already installed.")
    if os.geteuid() != 0:
        print_red(
            "Nua bootstrap script requires root privileges.\n"
            "Please try again, this time using 'sudo'. Exiting."
        )
        sys.exit(1)
    bootstrap()


def bootstrap():
    install_packages()
    create_nua_user()
    create_nua_venv()
    install_nginx()
    # create_nua_key()
    # create_ssl_key()


def install_packages():
    print_magenta("Installation of base packages:")
    install_package_list(HOST_PACKAGES)


def create_nua_user():
    if not user_exists("nua"):
        print_magenta("Creation of user 'nua'")
        cmd = "useradd --inactive -1 -G sudo,docker -m -s /bin/bash -U nua"
        sh(cmd)
    record_nua_home()
    nua_full_sudoer()


def nua_full_sudoer():
    print_magenta("Modifying /etc/sudoers for user 'nua' (full access with no passwd)")
    header = "# Nua: full access for Nua user:\n"
    # check already done:
    if string_in("/etc/sudoers", header):
        print_magenta("Prior changes found: do nothing")
        return
    with open("/etc/sudoers", "a") as sudofile:
        sudofile.write("\n")
        sudofile.write(header)
        sudofile.write("nua ALL=(ALL) NOPASSWD:ALL\n")


def record_nua_home():
    nua_home = str(Path("~nua").expanduser())
    if not nua_home:
        raise ValueError("Something weird append: can not find HOME of 'nua'")
    NUA_ENV["NUA_HOME"] = nua_home


def create_nua_venv():
    print_magenta("Creation of Python virtual env for 'nua'")
    # assuming we already did check we have python >= 3.10
    vname = "nua310"
    home = Path("~nua").expanduser()
    venv_path = home / vname
    if venv_path.is_dir():
        print_red(f"Prior {venv_path} found: do nothing")
        return
    os.chdir(home)
    venv.create(venv_path, with_pip=True)
    chown_r(venv_path, "nua", "nua")
    header = "# Nua python virtual env:\n"
    if not string_in(".bashrc", header):
        with open(".bashrc", "a") as bashrc:
            bashrc.write(header)
            bashrc.write(f"source ~/{vname}/bin/activate\n")
    bin_py = venv_path / "bin" / "python"
    cmd = f"{bin_py} -m pip install -U pip"
    exec_as_nua(cmd)
    cmd = f"{bin_py} -m pip install -U setuptools"
    exec_as_nua(cmd)


def install_nginx():
    print_magenta("Installation of Nua nginx configuration")
    nginx_conf()
    nua_nginx_folders()
    nua_nginx_default()
    nginx_restart()


def nginx_conf():
    host_nginx_conf = Path("/etc/nginx/nginx.conf")
    back_nginx_conf = host_nginx_conf.parent / "nginx_conf.orig"
    orch_nginx_conf = (
        Path(__file__).parent.parent.resolve() / "config" / "nginx" / "nginx.conf"
    )
    if host_nginx_conf.is_file():
        if not back_nginx_conf.is_file():
            # do no overwrite prior backup
            host_nginx_conf.rename(back_nginx_conf)
    else:
        print_red(f"Warning: the default nginx.conf file was not found")
    copy2(orch_nginx_conf, host_nginx_conf.parent)
    os.chmod(host_nginx_conf, 0o644)
    environ_replace_in(host_nginx_conf, NUA_ENV)


def nua_nginx_folders():
    nua_nginx = Path(NUA_ENV["NUA_HOME"]) / "nginx"
    for path in (
        nua_nginx,
        nua_nginx / "conf.d",
        nua_nginx / "sites",
        nua_nginx / "www" / "html",
    ):
        mkdir_p(path)
        os.chmod(nua_nginx, 0o755)
    chown_r(nua_nginx, "nua", "nua")


def nua_nginx_default():
    default = Path(NUA_ENV["NUA_HOME"]) / "nginx" / "sites" / "default"
    default_src = (
        Path(__file__).parent.parent.resolve() / "config" / "nginx" / "default"
    )
    copy2(default_src, default.parent)
    os.chmod(default, 0o644)
    chown_r(default, "nua", "nua")
    environ_replace_in(default, NUA_ENV)


def nginx_restart():
    # assuming some recent ubuntu distribution:
    cmd = "systemctl restart nginx"
    if os.geteuid() == 0:
        sh(cmd)
    else:
        sh(f"sudo {cmd}")


if __name__ == "__main__":
    main()
