"""Nginx utils to install nginx config and adapt with app using nginx."""
import os
from importlib import resources as rso
from pathlib import Path
from pprint import pformat
from time import sleep

from nua.lib.actions import jinja2_render_from_str_template
from nua.lib.panic import info, vprint, vprint_green, vprint_magenta, warning
from nua.lib.shell import chown_r, mkdir_p, rm_fr, sh
from nua.lib.tool.state import verbosity

from .. import config, nua_env
from ..certbot.certbot import use_https

CONF_TEMPLATE = "nua.orchestrator.nginx.templates"

# TODO: located templates do not support the "ssl=False" flag
TEMPLATES = {
    "located_http": "http_located.j2",
    "located_https": "https_located.j2",
    "noloca_http": "http_not_located.j2",
    "noloca_https": "https_not_located.j2",
}


def template_content(filename: str) -> str:
    return rso.files(CONF_TEMPLATE).joinpath(filename).read_text(encoding="utf8")


def install_nua_nginx_default_site():
    default_path = nua_env.nginx_path() / "sites" / "default"
    default_template = template_content("default_site")
    jinja2_render_from_str_template(default_template, default_path, nua_env.as_dict())
    os.chmod(default_path, 0o644)


def clean_nua_nginx_default_site():
    """Remove previous nginx sites.

    Warning: only for user 'nua' or 'root'
    """
    nua_nginx_path = nua_env.nginx_path()
    sites_path = nua_nginx_path / "sites"
    rm_fr(sites_path)
    mkdir_p(sites_path)
    os.chmod(nua_nginx_path, 0o755)  # noqa:S103
    install_nua_nginx_default_site()


def _set_instances_proxy_auto_port(host: dict):
    for site in host["apps"]:
        ports = site["port"]
        for port in ports.values():
            if port["proxy"] == "auto":
                site["host_use"] = port["host_use"]
                break


def _set_located_port_list(host: dict):
    if not host["located"]:
        return
    ports_set = set()
    for app in host["apps"]:
        ports = app["port"]
        ports_set.update(ports.keys())
    host["ports_list"] = list(ports_set)


def read_nginx_template(host: dict) -> str:
    if host["located"]:
        located = "located"
    else:
        located = "noloca"
    if use_https():
        protocol = "https"
    else:
        protocol = "http"
    key = f"{located}_{protocol}"
    filename = TEMPLATES[key]
    return template_content(filename)


def configure_nginx_hostname(host: dict):
    """warning: only for user 'nua' or 'root'

    host format:
      {'hostname': 'test.example.com',
       'located': True,
       'apps': [{'domain': 'test.example.com/instance1',
                 'hostname': 'example.com',
                 'top_domain': 'example.com',
                 'image': 'flask-one:1.2-1',
                 'location': 'instance1'
                 'port': {
                      "80": {
                        'name': 'web'
                        'container': 80,
                        'host': 'auto',
                        'host_use': 8100,
                        'proxy': 'auto'},
                        ,
                        ]
                      }
                   },
                   ...
    """
    with verbosity(4):
        vprint("configure_nginx_hostname: host")
        vprint(pformat(host))
    _set_instances_proxy_auto_port(host)
    _set_located_port_list(host)
    nua_nginx_path = nua_env.nginx_path()
    template = read_nginx_template(host)
    dest_path = nua_nginx_path / "sites" / host["hostname"]
    if "host_use" in host["apps"][0]:
        _actual_configure_nginx_hostname(template, dest_path, host)
    else:
        warning(f"host '{host['hostname']}': no public HTTP port configured")
        dest_path.unlink(missing_ok=True)


def _actual_configure_nginx_hostname(
    template: str,
    dest_path: str | Path,
    host: dict,
):
    with verbosity(4):
        vprint_magenta(f"{host['hostname']} template:")
        vprint(template)
    with verbosity(2):
        info("Nginx configuration:", dest_path)
    jinja2_render_from_str_template(template, dest_path, host)
    if dest_path.exists():
        with verbosity(3):
            vprint("Nginx configuration content:")
            with open(dest_path, encoding="utf8") as rfile:
                vprint(rfile.read())
    else:
        warning(f"host '{host['hostname']}', Nginx configuration not created")
    os.chmod(dest_path, 0o644)


def chown_r_nua_nginx():
    if not os.getuid():
        chown_r(nua_env.nginx_path(), "nua", "nua")


def nginx_restart():
    # assuming some recent ubuntu distribution:
    delay = config.read("host", "nginx_wait_after_restart") or 1
    with verbosity(2):
        vprint_green("Restart Nginx")
    cmd = "systemctl restart nginx"
    if os.geteuid() == 0:
        sh(cmd, show_cmd=False)
    else:
        sh(f"sudo {cmd}", show_cmd=False)
    sleep(delay)