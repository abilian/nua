from copy import deepcopy
from typing import Any

from .exceptions import NuaConfigError


def normalize_env_values(env: dict[str, str | int | float | list]) -> dict[str, Any]:
    def normalize_env_leaf(value: Any) -> str:
        if isinstance(value, str):
            return value
        if isinstance(value, (int, float, list)):
            return str(value)
        raise NuaConfigError(f"ENV value has wrong type: '{value}'")

    validated: dict[str, str | dict] = {}
    for key, value in env.items():
        if isinstance(value, dict):
            validated[key] = {k: normalize_env_leaf(v) for k, v in value.items()}
        else:
            validated[key] = normalize_env_leaf(value)

    return deepcopy(validated)


def normalize_keys(provider: dict[str, Any]) -> None:
    for key, value in provider.items():
        if "_" in key:
            new_key = key.replace("_", "-")
            provider[new_key] = value
            del provider[key]


def ports_as_list(ports_dict: dict) -> list:
    keys = list(ports_dict.keys())
    for key in keys:
        ports_dict[key]["name"] = key
    return list(ports_dict.values())


def normalize_ports(port_list: list[dict]) -> list[dict]:
    for port in port_list:
        _normalize_port(port)
    return port_list


def _normalize_port(port: dict[str, Any]) -> None:
    try:
        # _normalize_port_item_web(port)
        _normalize_port_item_container(port)
        _normalize_port_item_host(port)
        _normalize_port_item_proxy(port)
        _set_web_flag(port)
        _normalize_port_item_protocol(port)
        _normalize_port_item_ssl(port)
    except NuaConfigError:
        print("--- Error in ports config: ---")
        print(port)
        raise


# def _normalize_port_item_web(port: dict[str, Any]) -> None:
#     name = port["name"].lower()
#     web = port["web"]
#     # special case if  name of port is web: force web to True, refuse False
#     if name == "web":
#         if web is False:
#             raise NuaConfigError(
#                 "port['web'] can not be False for the port named 'web'"
#             )
#         web = True
#     if web is None:
#         # Defaulting to False
#         # The rule is : for any port with name different of "web", it's
#         # mandatory to set the web key to True, or the port is not a
#         # proxyied by nginx (for security resaon)
#         web = False
#     port["web"] = web


def _normalize_port_item_container(port: dict[str, Any]) -> None:
    pass


def _normalize_port_item_host(port: dict[str, Any]) -> None:
    # if port["web"]:
    #     # allow either None or integer host port for web traffic
    #     return
    host = port["host"]
    if isinstance(host, dict):
        return
    # if not port["host"], requirements: either some web proxy or name
    # of port is web for # automatic proxy
    if not host and not port["proxy"] and port["name"].lower() != "web":
        raise NuaConfigError("port['host'] is required for non-web traffic")


def _normalize_port_item_proxy(port: dict[str, Any]) -> None:
    """A web port must have a proxy values, except for the "web" named port,
    which is automatic (so either proxied to 80 or 443).

    For a non web port (ie. mail on port 25), the proxy is not used currently
    (unless some firewall is configured in the future). But the 'host' port is
    required.
    So a port without proxy must have a host port.
    """
    proxy = port["proxy"]
    if isinstance(proxy, dict):
        return
    # if not port["web"]:
    #     # allow proxy defined or not
    #     return
    if not proxy and not port["host"] and port["name"].lower() != "web":
        raise NuaConfigError(
            (
                "Only port.web can have an automatic 'proxy' value, other web "
                "published ports muste provide a proxy number"
            )
        )


def _set_web_flag(port: dict[str, Any]) -> None:
    """Set the key 'web' to True if the port is meaned to be proxyied by nginx."""
    if port["name"].lower() == "web" or port["proxy"]:
        port["web"] = True
    else:
        port["web"] = False


def _normalize_port_item_protocol(port: dict[str, Any]) -> None:
    protocol = port["protocol"]
    if protocol is None:
        protocol = "tcp"
    protocol = str(protocol).lower().strip()
    if protocol not in {"tcp", "udp"}:
        raise NuaConfigError(
            "port['protocol'] must be 'tcp' or 'udp' (default is 'tcp')"
        )
    port["protocol"] = protocol


def _normalize_port_item_ssl(port: dict[str, Any]) -> None:
    ssl = port["ssl"]
    if ssl is None:
        ssl = True
    port["ssl"] = ssl
