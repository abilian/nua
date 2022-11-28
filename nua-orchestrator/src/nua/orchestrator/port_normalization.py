from pprint import pformat


def ports_as_dict(port_list: list) -> dict:
    """replace ports list by a dict with container port as key.

    (use str key because later conversion to json)
    """
    return {str(port["container"]): port for port in port_list}


def normalize_ports(port_list: list, default_proxy: str):
    for port in port_list:
        _normalize_port(port, default_proxy)


def _normalize_port(port: dict, default_proxy: str):
    try:
        if not isinstance(port, dict):
            raise ValueError(" 'port' must be a dict")
        _normalize_port_item_container(port)
        _normalize_port_item_host(port)
        _normalize_port_item_protocol(port)
        _normalize_port_item_proxy(port, default_proxy)
    except ValueError:
        print("--- Error in ports config: ---")
        print(pformat(port))
        raise


def _normalize_port_item_container(port: dict):
    if "container" not in port:
        raise ValueError("Missing 'container' key in port configuration")
    try:
        cont = int(port["container"])
    except (ValueError, TypeError):
        raise ValueError("port['container'] value must be an integer")
    port["container"] = cont


def _normalize_port_item_host(port: dict):
    host = str(port.get("host", "auto")).lower().strip()
    if host == "auto":
        port["host"] = "auto"
        return
    try:
        host = int(host)
    except (ValueError, TypeError):
        raise ValueError("port['host'] value must be an integer if not 'auto'")
    port["host"] = host


def _normalize_port_item_protocol(port: dict):
    proto = str(port.get("protocol", "tcp")).lower().strip()
    if proto not in {"tcp", "udp"}:
        raise ValueError("port['protocol'] must be 'tcp' or 'udp' (default is 'tcp')")
    port["protocol"] = proto


def _normalize_port_item_proxy(port: dict, default_proxy: str):
    # fixme: currently only one proxy is managed by nginx configuration
    proxy = str(port.get("proxy", default_proxy)).lower().strip()
    name = port["name"]
    if proxy == "auto" and name != "web":
        raise ValueError("Only port.web can have an 'proxy' = 'auto' value")
    if proxy in {"auto", "none"}:
        port["proxy"] = proxy
        return
    try:
        proxy = int(proxy)
    except (ValueError, TypeError):
        raise ValueError("'proxy' value must be: an integer or 'auto' or 'none'")
    port["proxy"] = proxy
