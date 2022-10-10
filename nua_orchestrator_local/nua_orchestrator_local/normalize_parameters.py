"""Nua main scripts.

Rem: maybe need to refactor the "site" thing into a class and refactor a lot
"""
from pprint import pformat


def normalize_deploy_sites(deploy_sites: dict):
    """Check config syntax, replace missing informations by defaults."""
    for site in deploy_sites["site"]:
        try:
            _normalize_syntax_site(site)
        except ValueError:
            print("--- Error in site config: ---")
            print(pformat(site))
            raise


def _normalize_syntax_site(site: dict):
    if "image" not in site:
        raise ValueError("Missing 'image' key")
    if "domain" not in site:
        raise ValueError("Missing 'domain' key")
    normalize_ports(site)


def normalize_ports(site: dict):
    if "ports" not in site:
        site["ports"] = {}  # convert to dict
        return
    if not isinstance(site["ports"], list):
        raise ValueError("'ports' must be a list")
    for index, port_item in enumerate(site["ports"]):
        try:
            _normalize_port_item(index, port_item)
        except ValueError:
            print("--- Error in ports config: ---")
            print(pformat(port_item))
            raise
    # replace ports list by a dict with container port as key
    # use str key because later conversion to json
    site["ports"] = {str(port["container"]): port for port in site["ports"]}


def _normalize_port_item(index: int, port: dict):
    _normalize_port_item_container(port)
    _normalize_port_item_host(index, port)
    _normalize_port_item_protocol(port)
    _normalize_port_item_proxy(index, port)


def _normalize_port_item_container(port: dict):
    if "container" not in port:
        raise ValueError("Missing 'container' key in ports configuration")
    try:
        cont = int(port["container"])
    except (ValueError, TypeError):
        raise ValueError("'container' value must be an integer")
    port["container"] = cont


def _normalize_port_item_host(index: int, port: dict):
    host = str(port.get("host", "auto")).lower().strip()
    if host == "auto":
        if index > 0:
            raise ValueError("Only the first port can have an 'host' = 'auto' value")
        else:
            port["host"] = "auto"
        return
    try:
        host = int(host)
    except (ValueError, TypeError):
        raise ValueError("'host' value must be an integer if not 'auto'")
    port["host"] = host


def _normalize_port_item_protocol(port: dict):
    proto = str(port.get("protocol", "tcp")).lower().strip()
    if proto not in {"tcp", "udp"}:
        raise ValueError("'protocol' must be 'tcp' or 'udp' (default is 'tcp')")
    port["protocol"] = proto


def _normalize_port_item_proxy(index: int, port: dict):
    # fixme: currently only one proxy is managed by nginx configuration
    proxy = str(port.get("proxy", "auto")).lower().strip()
    if proxy == "auto" and index > 0:
        raise ValueError("Only the first port can have an 'proxy' = 'auto' value")
    if proxy in {"auto", "none"}:
        port["proxy"] = proxy
        return
    try:
        proxy = int(proxy)
    except (ValueError, TypeError):
        raise ValueError("'proxy' value must be: an integer or 'auto' or 'none'")
    port["proxy"] = proxy
