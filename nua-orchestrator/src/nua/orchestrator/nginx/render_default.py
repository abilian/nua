"""Nginx utils to install nginx config and adapt with app using nginx."""
import os
from importlib import resources as rso

from nua.lib.actions import jinja2_render_from_str_template
from nua.lib.shell import chown_r, mkdir_p, rm_fr

from ..nua_env import nua_env

CONF_TEMPLATE = "nua.orchestrator.nginx.templates"


def template_content(filename: str) -> str:
    return rso.files(CONF_TEMPLATE).joinpath(filename).read_text(encoding="utf8")


def install_nua_nginx_default_site() -> None:
    default_path = nua_env.nginx_path() / "sites" / "default"
    default_template = template_content("default_site")
    jinja2_render_from_str_template(default_template, default_path, nua_env.as_dict())
    os.chmod(default_path, 0o644)


def clean_nua_nginx_default_site() -> None:
    """Remove previous nginx sites.

    Warning: only for user 'nua' or 'root'
    """
    nua_nginx_path = nua_env.nginx_path()
    sites_path = nua_nginx_path / "sites"
    rm_fr(sites_path)
    mkdir_p(sites_path)
    os.chmod(nua_nginx_path, 0o755)  # noqa:S103
    install_nua_nginx_default_site()


def chown_r_nua_nginx() -> None:
    if not os.getuid():
        chown_r(nua_env.nginx_path(), "nua", "nua")
