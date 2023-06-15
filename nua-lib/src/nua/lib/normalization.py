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


def normalize_scheme(scheme: dict[str, Any]) -> dict[str, Any]:
    validated: dict[str, Any] = {}
    for key, value in scheme.items():
        if "_" in key:
            new_key = key.replace("_", "-")
        else:
            new_key = key
        validated[new_key] = value
    return deepcopy(validated)


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
        _normalize_port_item_container(port)
        _normalize_port_item_host(port)
        _normalize_port_item_protocol(port)
        _normalize_port_item_proxy(port)
        _normalize_port_item_ssl(port)
    except NuaConfigError:
        print("--- Error in ports config: ---")
        print(port)
        raise


def _normalize_port_item_container(port: dict[str, Any]) -> None:
    pass


def _normalize_port_item_host(port: dict[str, Any]) -> None:
    pass


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


def _normalize_port_item_proxy(port: dict[str, Any]) -> None:
    proxy = port["proxy"]
    if isinstance(proxy, dict):
        return
    if proxy is None:
        name = port["name"]
        if name != "web":
            raise NuaConfigError("Only port.web can have an automatic 'proxy' value")


def _normalize_port_item_ssl(port: dict[str, Any]) -> None:
    ssl = port["ssl"]
    if ssl is None:
        ssl = True
    port["ssl"] = ssl
