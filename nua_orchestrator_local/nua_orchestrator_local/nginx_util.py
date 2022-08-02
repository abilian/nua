"""Nginx utils to install nginx config and adapt with app using nginx."""
import os
from pathlib import Path
from shutil import copy2

from . import nua_env
from .actions import environ_replace_in
from .rich_console import print_magenta, print_red
from .shell import chown_r, mkdir_p, sh


def install_nginx():
    print_magenta("Installation of Nua nginx configuration")
    replace_nginx_conf()
    make_nua_nginx_folders()
    install_nua_nginx_default()
    nginx_restart()


def replace_nginx_conf():
    # assume standard linux distribution path:
    host_nginx_conf = Path("/etc/nginx/nginx.conf")
    back_nginx_conf = host_nginx_conf.parent / "nginx_conf.orig"
    orch_nginx_conf = (
        Path(__file__).parent.resolve() / "config" / "nginx" / "nginx.conf"
    )
    if host_nginx_conf.is_file():
        if not back_nginx_conf.is_file():
            # do no overwrite prior backup
            host_nginx_conf.rename(back_nginx_conf)
    else:
        print_red("Warning: the default host nginx.conf file was not found")
    copy2(orch_nginx_conf, host_nginx_conf.parent)
    os.chmod(host_nginx_conf, 0o644)
    environ_replace_in(host_nginx_conf, nua_env.as_dict())


def make_nua_nginx_folders():
    nua_nginx = nua_env.nginx_path()
    for path in (
        nua_nginx,
        nua_nginx / "conf.d",
        nua_nginx / "sites",
        nua_nginx / "www" / "html",
    ):
        mkdir_p(path)
        os.chmod(nua_nginx, 0o755)  # noqa:S103
        # S103=Chmod setting a permissive mask 0o755 on file
    chown_r(nua_nginx, "nua", "nua")


def install_nua_nginx_default():
    default = nua_env.nginx_path() / "sites" / "default"
    default_src = Path(__file__).parent.resolve() / "config" / "nginx" / "default"
    copy2(default_src, default.parent)
    os.chmod(default, 0o644)
    chown_r(default, "nua", "nua")
    environ_replace_in(default, nua_env.as_dict())


def nginx_restart():
    # assuming some recent ubuntu distribution:
    cmd = "systemctl restart nginx"
    if os.geteuid() == 0:
        sh(cmd)
    else:
        sh(f"sudo {cmd}")
