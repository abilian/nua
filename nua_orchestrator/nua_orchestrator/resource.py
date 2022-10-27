from typing import Callable

from .port_normalization import normalize_ports, ports_as_dict
from .volume_normalization import normalize_volumes


class Resource(dict):
    MANDATORY_KEYS = ("image", "type")

    def __init__(self, site_dict: dict):
        super().__init__(site_dict)

    def check_valid(self):
        self._check_mandatory()
        self._normalize_ports()
        self._normalize_volumes()

    @property
    def type(self) -> str:
        return self["type"]

    @type.setter
    def type(self, tpe: str):
        self["type"] = tpe

    @property
    def image(self) -> str:
        return self["image"]

    @image.setter
    def image(self, image: str):
        self["image"] = image

    @property
    def domain(self) -> str:
        return self.get("domain", "")

    @domain.setter
    def domain(self, domain: str):
        self["domain"] = domain

    @property
    def ports(self) -> list | dict:
        return self["ports"]

    @ports.setter
    def ports(self, ports: list | dict):
        self["ports"] = ports

    @property
    def volume(self) -> list:
        return self.get("volume", [])

    @volume.setter
    def volume(self, volumes: list):
        self["volume"] = volumes

    @property
    def hostname(self) -> str:
        return self.get("hostname", "")

    @hostname.setter
    def hostname(self, hostname: str):
        self["hostname"] = hostname

    @property
    def run_params(self) -> dict:
        return self.get("run_params", {})

    @run_params.setter
    def run_params(self, run_params: dict):
        self["run_params"] = run_params

    @property
    def run_env(self) -> dict:
        return self.get("run_env", {})

    @run_env.setter
    def run_env(self, run_env: dict):
        self["run_env"] = run_env

    def set_ports_as_dict(self):
        """replace ports list by a dict with container port as key

        (use str key because later conversion to json)"""
        ports_dict = ports_as_dict(self.ports)
        self.ports = ports_dict

    def _check_mandatory(self):
        for key in self.MANDATORY_KEYS:
            if not self.get(key):
                raise ValueError(f"Site configuration missing '{key}' key")

    def _normalize_ports(self):
        if "ports" not in self:
            self.ports = []
            return
        if not isinstance(self.ports, list):
            raise ValueError("Site['ports'] must be a list")
        self.ports = [p for p in self.ports if p]
        normalize_ports(self.ports)

    def used_ports(self) -> set[int]:
        used = set()
        # when method is used, ports became a dict:
        for port in self.ports.values():
            if not port:  # could be an empty {} ?
                continue
            host = port["host"]
            # normalization done: host is present and either 'auto' or an int
            if isinstance(host, int):
                used.add(host)
        return used

    def allocate_auto_ports(self, allocator: Callable):
        if not self.ports:
            return
        # when method is used, ports became a dict:
        for port in self.ports.values():
            if port["host"] == "auto":
                port["host_port"] = allocator()
            else:
                port["host_port"] = port["host"]

    def ports_as_docker_params(self) -> dict:
        cont_ports = {}
        for port in self.ports.values():
            cont_ports[f"{port['container']}/{port['protocol']}"] = port["host_port"]
        return cont_ports

    def _normalize_volumes(self):
        if "volume" not in self:
            self.volume = []
            return
        if not isinstance(self.volume, list):
            raise ValueError("Site['volume'] must be a list")
        self.volume = [v for v in self.volume if v]
        normalize_volumes(self.volume)

    def update_volume_from_instance(self, instance_dict: dict) -> list:
        self.volume = self._merge_volumes_lists(instance_dict, reverse=True)

    def rebased_volumes_upon_package_conf(self, package_dict: dict):
        """warning: here, no update of self data"""
        return self._merge_volumes_lists(package_dict, reverse=False)

    def _merge_volumes_lists(self, other_dict: dict, reverse: bool):
        base = other_dict.get("volume") or []
        base = [v for v in base if v]
        if not base:
            return []
        merge_dict = {}
        merge_list = base + self.volume
        if reverse:
            merge_list.reverse()
        for vol in base + self.volume:
            # the unicity key for volume is 'source'
            merge_dict[vol["source"]] = vol
        return list(merge_dict.values())
