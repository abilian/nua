"""Nginx utils to install nginx config and adapt with app using nginx."""
import os
from pathlib import Path

from . import nua_env
from .actions import jinja2_render_file
from .rich_console import print_magenta, print_red
from .shell import chown_r, mkdir_p, sh


def install_nginx():
    print_magenta("Installation of Nua nginx configuration")
    replace_nginx_conf()
    make_nua_nginx_folders()
    install_nua_nginx_default_site()
    install_nua_nginx_default_index_html()
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
    jinja2_render_file(orch_nginx_conf, host_nginx_conf, nua_env.as_dict())
    os.chmod(host_nginx_conf, 0o644)


def make_nua_nginx_folders():
    nua_nginx = nua_env.nginx_path()
    for path in (
        nua_nginx,
        nua_nginx / "conf.d",
        nua_nginx / "sites",
        nua_nginx / "www" / "html",
        nua_nginx / "www" / "html" / "css",
    ):
        mkdir_p(path)
        os.chmod(nua_nginx, 0o755)  # noqa:S103
        # S103=Chmod setting a permissive mask 0o755 on file
    chown_r(nua_nginx, "nua", "nua")
    chown_r(nua_nginx / "www", "www-data", "www-data")


def install_nua_nginx_default_site():
    default = nua_env.nginx_path() / "sites" / "default"
    default_src = Path(__file__).parent.resolve() / "config" / "nginx" / "default"
    jinja2_render_file(default_src, default, nua_env.as_dict())
    os.chmod(default, 0o644)
    chown_r(default, "nua", "nua")


def install_nua_nginx_default_index_html():
    page = nua_env.nginx_path() / "www" / "html" / "index.html"
    page_src = (
        Path(__file__).parent.resolve() / "config" / "nginx" / "html" / "index.html"
    )
    jinja2_render_file(page_src, page, nua_env.as_dict())
    os.chmod(page, 0o644)
    chown_r(page, "www-data", "www-data")


def nginx_restart():
    # assuming some recent ubuntu distribution:
    cmd = "systemctl restart nginx"
    if os.geteuid() == 0:
        sh(cmd)
    else:
        sh(f"sudo {cmd}")
