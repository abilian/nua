"""Nginx utils to install nginx config and adapt with app using nginx."""
import os
from importlib import resources as rso
from pathlib import Path
from pprint import pformat
from time import sleep

from nua.lib.actions import jinja2_render_from_str_template
from nua.lib.console import print_magenta
from nua.lib.panic import info, vprint, vprint_green, vprint_magenta, warning
from nua.lib.shell import chown_r, mkdir_p, rm_fr, sh
from nua.lib.tool.state import verbosity

from . import config, nua_env
from .certbot.certbot import use_https

CONF_TEMPLATE = "nua.orchestrator.templates.nginx.template"
CONF_HTML = "nua.orchestrator.templates.nginx.html"
TEMPLATES = {
    "mono_located_http": "domain_located_template",
    "mono_located_https": "unimplemented",  # requires certbot --redirect option
    "mono_noloca_http": "_good_domain_not_located_template",
    "mono_noloca_https": "https_not_located.j2",  # did require certbot --redirect
    "multi_located_http": "wip_certbot_is_broken",
    "multi_located_https": "wip_certbot_is_broken",
    "multi_noloca_http": "http_domain_not_located_template",
    "multi_noloca_https": "https_not_located.j2",
}


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
    orch_nginx_conf = (
        rso.files(CONF_TEMPLATE).joinpath("nginx.conf").read_text(encoding="utf8")
    )
    if host_nginx_conf.is_file():
        if not back_nginx_conf.is_file():
            # do no overwrite prior backup
            host_nginx_conf.rename(back_nginx_conf)
    else:
        warning("the default host nginx.conf file was not found")
    jinja2_render_from_str_template(orch_nginx_conf, host_nginx_conf, nua_env.as_dict())
    os.chmod(host_nginx_conf, 0o644)


def make_nua_nginx_folders():
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


def install_nua_nginx_default_site():
    default = nua_env.nginx_path() / "sites" / "default"
    default_template = (
        rso.files(CONF_TEMPLATE).joinpath("default_site").read_text(encoding="utf8")
    )
    jinja2_render_from_str_template(default_template, default, nua_env.as_dict())
    os.chmod(default, 0o644)


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


def _set_instances_proxy_port(host: dict):
    # FIXME: update templates to accept several proxyied ports
    for site in host["apps"]:
        ports = site["port"]
        for port in ports.values():
            if port["proxy"] == "auto":
                site["host_use"] = port["host_use"]
                break


def read_nginx_template(host: dict) -> str:
    if len(host["apps"][0]["port"]) > 1:
        ports = "multi"
    else:
        ports = "mono"
    if host["located"]:
        loca = "located"
    else:
        loca = "noloca"
    if use_https():
        proto = "https"
    else:
        proto = "http"
    key = f"{ports}_{loca}_{proto}"
    filename = TEMPLATES[key]
    return rso.files(CONF_TEMPLATE).joinpath(filename).read_text(encoding="utf8")


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
    _set_instances_proxy_port(host)
    # later: see for port on other :port interfaces
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


def install_nua_nginx_default_index_html():
    page = nua_env.nginx_path() / "www" / "html" / "index.html"
    page_src = rso.files(CONF_HTML).joinpath("index.html").read_text(encoding="utf8")
    jinja2_render_from_str_template(page_src, page, nua_env.as_dict())
    os.chmod(page, 0o644)
    chown_r(page, "www-data", "www-data")


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
