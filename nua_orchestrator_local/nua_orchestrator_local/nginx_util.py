"""Nginx utils to install nginx config and adapt with app using nginx."""
import os
from pathlib import Path
from time import sleep

from . import config, nua_env
from .actions import jinja2_render_file
from .rich_console import print_magenta, print_red
from .shell import chown_r, mkdir_p, rm_fr, sh
from .state import verbosity

CONF_NGINX = Path(__file__).parent.resolve() / "config" / "nginx"


def install_nginx():
    print_magenta("Installation of Nua nginx configuration")
    replace_nginx_conf()
    make_nua_nginx_folders()
    install_nua_nginx_default_site()
    install_nua_nginx_default_index_html()
    chown_r_nua_nginx()
    nginx_restart()


def replace_nginx_conf():
    # assume standard linux distribution path:
    host_nginx_conf = Path("/etc/nginx/nginx.conf")
    back_nginx_conf = host_nginx_conf.parent / "nginx_conf.orig"
    orch_nginx_conf = CONF_NGINX / "template" / "nginx.conf"
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
    default_template = CONF_NGINX / "template" / "default_site"
    jinja2_render_file(default_template, default, nua_env.as_dict())
    os.chmod(default, 0o644)


def clean_nua_nginx_default_site():
    """Remove previous nginx sites.

    Warning: only for user 'nua' or 'root'"""
    nua_nginx = nua_env.nginx_path()
    sites = nua_nginx / "sites"
    rm_fr(sites)
    mkdir_p(sites)
    os.chmod(nua_nginx, 0o755)  # noqa:S103
    install_nua_nginx_default_site()


def configure_nginx_hostname(host: dict):
    """warning: only for user 'nua' or 'root'

    host format:
      {'hostname': 'test.example.com',
       'prefixed': True,
       'sites': [{'domain': 'test.example.com/instance1',
                   'image': 'flask-one:1.2-1',
                   'port': 'auto',
                   'actual_port': 8100,
                   'prefix': 'instance1'
                   },
                   ...
    """
    nua_nginx = nua_env.nginx_path()
    if host["prefixed"]:
        template = CONF_NGINX / "template" / "domain_prefixed_template"
    else:
        template = CONF_NGINX / "template" / "domain_not_prefixed_template"
    dest_path = nua_nginx / "sites" / host["hostname"]
    if verbosity(2):
        print(host["hostname"], "template:", template)
        print(host["hostname"], "target  :", dest_path)
    jinja2_render_file(template, dest_path, host)
    if verbosity(2):
        if not dest_path.exists():
            print(host["hostname"], "Warning: target not created")
        else:
            print(host["hostname"], "content:")
            with open(dest_path, "r", encoding="utf8") as rfile:
                print(rfile.read())
    os.chmod(dest_path, 0o644)


def chown_r_nua_nginx():
    if not os.getuid():
        chown_r(nua_env.nginx_path(), "nua", "nua")


def install_nua_nginx_default_index_html():
    page = nua_env.nginx_path() / "www" / "html" / "index.html"
    page_src = CONF_NGINX / "html" / "index.html"
    jinja2_render_file(page_src, page, nua_env.as_dict())
    os.chmod(page, 0o644)
    chown_r(page, "www-data", "www-data")


def nginx_restart():
    # assuming some recent ubuntu distribution:
    delay = config.read("host", "nginx_wait_after_restart") or 1
    cmd = "systemctl restart nginx"
    if os.geteuid() == 0:
        sh(cmd)
    else:
        sh(f"sudo {cmd}")
    sleep(delay)
