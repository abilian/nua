"""Nginx utils to install nginx config and adapt with app using nginx."""
import os
from importlib import resources as rso
from pathlib import Path

from nua.lib.actions import jinja2_render_from_str_template
from nua.lib.console import print_magenta
from nua.lib.panic import warning
from nua.lib.shell import chown_r, mkdir_p

from ..nua_env import nua_env
from .commands import nginx_restart
from .render_default import (
    chown_r_nua_nginx,
    install_nua_nginx_default_site,
    template_content,
)

CONF_HTML = "nua.orchestrator.nginx.html"


def install_nginx() -> None:
    print_magenta("Installation of Nua nginx configuration")
    replace_nginx_conf()
    make_nua_nginx_folders()
    install_nua_nginx_default_site()
    install_nua_nginx_default_index_html()
    chown_r_nua_nginx()
    nginx_restart()


def replace_nginx_conf() -> None:
    # assume standard linux distribution path:
    host_nginx_conf = Path("/etc/nginx/nginx.conf")
    back_nginx_conf = host_nginx_conf.parent / "nginx_conf.orig"
    orch_nginx_conf = template_content("nginx.conf")
    if host_nginx_conf.is_file():
        if not back_nginx_conf.is_file():
            # do no overwrite prior backup
            host_nginx_conf.rename(back_nginx_conf)
    else:
        warning("the default host nginx.conf file was not found")
    jinja2_render_from_str_template(orch_nginx_conf, host_nginx_conf, nua_env.as_dict())
    os.chmod(host_nginx_conf, 0o644)


def make_nua_nginx_folders() -> None:
    nua_nginx_path = nua_env.nginx_path()
    for path in (
        nua_nginx_path,
        nua_nginx_path / "conf.d",
        nua_nginx_path / "sites",
        nua_nginx_path / "www" / "html",
        nua_nginx_path / "www" / "html" / "css",
    ):
        mkdir_p(path)
        os.chmod(nua_nginx_path, 0o755)  # noqa:S103
        # S103=Chmod setting a permissive mask 0o755 on file
    chown_r(nua_nginx_path, "nua", "nua")
    chown_r(nua_nginx_path / "www", "www-data", "www-data")


def install_nua_nginx_default_index_html() -> None:
    page = nua_env.nginx_path() / "www" / "html" / "index.html"
    page_src = rso.files(CONF_HTML).joinpath("index.html").read_text(encoding="utf8")
    jinja2_render_from_str_template(page_src, page, nua_env.as_dict())
    os.chmod(page, 0o644)
    chown_r(page, "www-data", "www-data")
