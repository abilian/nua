from pprint import pformat


def ports_as_dict(port_list: list) -> dict:
    """Replace ports list by a dict with container port as key.

    (Use str key because later conversion to json)
    """
    return {str(port["container"]): port for port in port_list}


def ports_assigned(ports: list) -> set[int]:
    used = set()
    for port in ports:
        if not port:  # could be an empty {} ?
            continue
        host = port["host"]
        # normalization done: host is present and either 'auto' or an int
        if isinstance(host, int):
            used.add(host)
        # if proxy is hard coded (when multiple port are open),
        # add it to the list
        proxy = port["proxy"]
        if isinstance(proxy, int):
            used.add(proxy)
    return used


def ports_as_docker_parameters(ports: list) -> dict:
    return {
        f"{port['container']}/{port['protocol']}": port["host_use"] for port in ports
    }


def ports_as_list(ports_dict: dict) -> list:
    keys = list(ports_dict.keys())
    for key in keys:
        ports_dict[key]["name"] = key
    return list(ports_dict.values())


def rebase_ports_on_defaults(defaults_ports: list, update_ports: list) -> list:
    defaults = {p["name"]: p for p in defaults_ports}
    updates = {p["name"]: p for p in update_ports}
    defaults.update(updates)
    return list(defaults.values())


def normalize_ports(port_list: list):
    for port in port_list:
        _normalize_port(port)


def normalize_ports_list(port_list: list) -> list:
    for port in port_list:
        _normalize_port(port)
    return port_list


def _normalize_port(port: dict):
    try:
        if not isinstance(port, dict):
            raise ValueError(" 'port' must be a dict")
        _normalize_port_item_container(port)
        _normalize_port_item_host(port)
        _normalize_port_item_protocol(port)
        _normalize_port_item_proxy(port)
        _normalize_port_item_ssl(port)
    except ValueError:
        print("--- Error in ports config: ---")
        print(pformat(port))
        raise


def _normalize_port_item_container(port: dict):
    if "container" not in port:
        raise ValueError("Missing 'container' key in port configuration")
    if isinstance(port["container"], dict):
        return
    try:
        container = int(port["container"])
    except (ValueError, TypeError):
        raise ValueError("port['container'] value must be an integer")
    port["container"] = container


def _normalize_port_item_host(port: dict):
    host = port.get("host", "auto")
    if isinstance(host, dict):
        return
    host = str(host).lower().strip()
    if host == "auto":
        port["host"] = "auto"
        return
    try:
        int_host = int(host)
    except (ValueError, TypeError):
        raise ValueError("port['host'] value must be an integer if not 'auto'")
    port["host"] = int_host


def _normalize_port_item_protocol(port: dict):
    protocol = str(port.get("protocol", "tcp")).lower().strip()
    if protocol not in {"tcp", "udp"}:
        raise ValueError("port['protocol'] must be 'tcp' or 'udp' (default is 'tcp')")
    port["protocol"] = protocol


def _normalize_port_item_proxy(port: dict):
    proxy = port.get("proxy", "auto")
    if isinstance(proxy, dict):
        return
    proxy = str(proxy).lower().strip()  # proxy auto ~ 80, 443
    name = port["name"]
    if proxy == "auto" and name != "web":
        raise ValueError("Only port.web can have an 'proxy' = 'auto' value")
    if proxy in {"auto", "none"}:
        port["proxy"] = proxy
        return
    try:
        int_proxy = int(proxy)
    except (ValueError, TypeError):
        raise ValueError("'proxy' value must be: an integer or 'auto' or 'none'")
    port["proxy"] = int_proxy


def _normalize_port_item_ssl(port: dict):
    ssl = bool(port.get("ssl", True))
    port["ssl"] = ssl
