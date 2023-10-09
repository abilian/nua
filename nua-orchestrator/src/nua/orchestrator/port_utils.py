def ports_as_dict(port_list: list[dict]) -> dict:
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


def rebase_ports_on_defaults(defaults_ports: list, update_ports: list) -> list:
    defaults = {p["name"]: p for p in defaults_ports}
    updates = {p["name"]: p for p in update_ports}
    defaults.update(updates)
    return list(defaults.values())
