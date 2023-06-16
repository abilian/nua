"""Nginx utils to install nginx config and adapt with app using nginx."""
import os
from importlib import resources as rso
from pathlib import Path
from pprint import pformat
from typing import Any

from nua.lib.actions import jinja2_render_from_str_template
from nua.lib.panic import bold_debug, debug, info, warning
from nua.lib.shell import chown_r, mkdir_p, rm_fr
from nua.lib.tool.state import verbosity

from .. import nua_env
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


def _set_instances_proxy_auto_port(host: dict[str, Any]) -> None:
    """Set the port used for public HTTP(S) as app["host_use"].

    The port used is the first with None proxy -> will be proxied
    on 443 or 80."""
    internal_apps = True  # if the app has no public web port
    for app in host["apps"]:
        list_of_ports = app["port_list"]
        for port in list_of_ports:
            if port["proxy"] is None:
                app["host_use"] = port["host_use"]
                internal_apps = False
                break
    host["internal"] = internal_apps


def _set_located_port_list(host: dict[str, Any]) -> None:
    """For app using a located scheme (https://xx.example.tld/location/)"""
    if not host["located"]:
        return
    ports_set = set()
    for app in host["apps"]:
        list_of_ports = app["port_list"]
        for port in list_of_ports:
            ports_set.add(port["container"])
    host["located_ports_list"] = list(ports_set)


def read_nginx_template(host: dict[str, Any]) -> str:
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


def configure_nginx_hostname(host: dict[str, Any]) -> None:
    """warning: only for user 'nua' or 'root'

    host format:
      {'hostname': 'test.example.com',
       'located': True,
       'apps': [{'domain': 'test.example.com/instance1',
                 'hostname': 'example.com',
                 'top_domain': 'example.com',
                 'image': 'flask-one:1.2-1',
                 'location': 'instance1'
                 'port': {},
                 'port_list': [{'container': 3000,
                                  'host': None,
                                  'host_use': 8101,
                                  'name': 'web',
                                  'protocol': 'tcp',
                                  'proxy': None,
                                  'ssl': True}],

                   ...
     or:
        {'apps': [{'backup': {},
                    'domain': 'test1.yerom.xyz',
                    'env': {},
                    'healthcheck': {},
                    'hostname': 'test1.yerom.xyz',
                    ...
                    'label_id': 'nopub',
                    'port': {},
                    'port_list': [{'container': 8764,
                                    'host': None,
                                    'host_use': 8100,
                                    'name': 'one',
                                    'protocol': 'tcp',
                                    'proxy': 8764,
                                    'ssl': True},
                                {'container': 8765,
                                    'host': None,
                                    'host_use': 8101,
                                    'name': 'two',
                                    'protocol': 'tcp',
                                    'proxy': 8765,
                                    'ssl': False}],
                     ...
                    'top_domain': 'yerom.xyz',
                    'type': 'nua-site',
                    'volume': []}],
        'hostname': 'test1.yerom.xyz',
        'located': False}

    """
    with verbosity(4):
        bold_debug("configure_nginx_hostname: host")
        debug(pformat(host))
    _set_instances_proxy_auto_port(host)
    _set_located_port_list(host)
    nua_nginx_path = nua_env.nginx_path()
    dest_path = nua_nginx_path / "sites" / host["hostname"]
    if host["internal"]:
        return _internal_deployment(host, dest_path)
    return _actual_configure_nginx_hostname(host, dest_path)


def _internal_deployment(host: dict[str, Any], dest_path: Path) -> None:
    warning(f"host '{host['hostname']}': no HTTP(S) port configured")
    dest_path.unlink(missing_ok=True)


def remove_nginx_configuration_hostname(stop_domain: str) -> None:
    """Remove configuration for dommain.

    warning: only for user 'nua' or 'root'
    """
    with verbosity(4):
        bold_debug("remove_nginx_configuration_hostname:")
        debug(stop_domain)
    nua_nginx_path = nua_env.nginx_path()
    dest_path = nua_nginx_path / "sites" / stop_domain
    dest_path.unlink(missing_ok=True)


def _actual_configure_nginx_hostname(
    host: dict[str, Any],
    dest_path: Path,
) -> None:
    template = read_nginx_template(host)
    with verbosity(4):
        bold_debug(f"{host['hostname']} template:")
        debug(template)
    with verbosity(1):
        info("Nginx configuration:", dest_path)
    jinja2_render_from_str_template(template, dest_path, host)
    if dest_path.exists():
        with verbosity(3):
            bold_debug("Nginx configuration content:")
            with open(dest_path, encoding="utf8") as rfile:
                debug(rfile.read())
    else:
        warning(f"host '{host['hostname']}', Nginx configuration failed")
    os.chmod(dest_path, 0o644)


def chown_r_nua_nginx() -> None:
    if not os.getuid():
        chown_r(nua_env.nginx_path(), "nua", "nua")
