from collections.abc import Callable
from copy import deepcopy

from nua.lib.panic import error, warning
from nua.lib.tool.state import verbosity

from .healthcheck import HealthCheck
from .port_normalization import normalize_ports, ports_as_dict
from .utils import sanitized_name
from .volume import Volume


class Resource(dict):
    def __init__(self, declaration: dict):
        super().__init__(declaration)
        if "requested_secrets" not in self:
            self.requested_secrets = []

    @classmethod
    def from_dict(cls, resource_dict: dict) -> "Resource":
        resource = cls({})
        for key, val in resource_dict.items():
            resource[key] = val
        resource["port"] = resource.get("port") or {}
        return resource

    def check_valid(self):
        self._check_mandatory()
        self._parse_run_env()
        self._parse_healthcheck()
        self._normalize_ports()
        self._normalize_volumes()

    @property
    def resources(self) -> list:
        """List of sub resources of the object.

        Warning: only Site upper class has an actual use of 'resources'.
        This sub class Resource will always provide an *empty*list
        """
        return []

    @resources.setter
    def resources(self, _resources: list):
        pass

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
    def service(self) -> str:
        return self["service"]

    @service.setter
    def service(self, service: str):
        self["service"] = service

    @property
    def assign(self) -> list:
        return self.get("assign", [])

    @assign.setter
    def assign(self, assign_list: list):
        self["assign"] = assign_list

    @property
    def domain(self) -> str:
        return self.get("domain", "")

    @domain.setter
    def domain(self, domain: str):
        self["domain"] = domain

    @property
    def port(self) -> list | dict:
        return self["port"]

    @port.setter
    def port(self, ports: list | dict):
        self["port"] = ports

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

    @property
    def base_name(self) -> str:
        return self.image.split("/")[-1].replace(":", "-")

    @property
    def image_id(self) -> str:
        return self.get("image_id", "")

    @image_id.setter
    def image_id(self, image_id: str):
        self["image_id"] = image_id

    @property
    def image_id_short(self) -> str:
        if self.image_id.startswith("sha256:"):
            return self.image_id[7:19]
        return self.image_id[:12]

    @property
    def container(self) -> str:
        return self.get("container", "")

    @container.setter
    def container(self, name: str):
        self["container"] = name

    @property
    def container_id(self) -> str:
        return self.get("container_id", "")

    @container_id.setter
    def container_id(self, container_id: str):
        self["container_id"] = container_id

    @property
    def container_id_short(self) -> str:
        if self.container_id.startswith("sha256:"):
            return self.container_id[7:19]
        return self.container_id[:12]

    @property
    def resource_name(self) -> str:
        return self.get("resource_name", "")

    @resource_name.setter
    def resource_name(self, resource_name: str):
        self["resource_name"] = resource_name

    @property
    def network_name(self) -> str:
        return self.get("network_name", "")

    @network_name.setter
    def network_name(self, name: str):
        if name:
            self["network_name"] = sanitized_name(name)
        else:
            self["network_name"] = ""

    @property
    def persistent(self) -> dict:
        if "persistent" not in self:
            self["persistent"] = {}
        return self["persistent"]

    @persistent.setter
    def persistent(self, persist: dict):
        self["persistent"] = deepcopy(persist)

    @property
    def healthcheck(self) -> dict:
        if "healthcheck" not in self:
            self["healthcheck"] = {}
        return self["healthcheck"]

    @healthcheck.setter
    def healthcheck(self, healthcheck: dict):
        self["healthcheck"] = healthcheck

    def set_ports_as_dict(self):
        """replace ports list by a dict with container port as key.

        (use str key because later conversion to json)
        """
        if not isinstance(self.port, dict):
            ports_dict = ports_as_dict(self.port)
            self.port = ports_dict
        for resource in self.resources:
            resource.set_ports_as_dict()

    def _check_mandatory(self):
        self._check_missing("type")
        if self["type"] == "local":
            self._check_missing("service")
        elif self["type"] == "docker":
            self._check_missing("image")

    def _check_missing(self, key: str):
        if key not in self:
            error(f"Site or Resource configuration missing '{key}' key")

    def _parse_run_env(self):
        run_env = self.run_env  # may contain dict of deprecated syntax
        env = self.get("run", {}).get("env", {})
        if not isinstance(env, dict):
            error("[run.env] must be a dict")
        run_env.update(env)
        self.run_env = run_env
        run = self.get("run", {})
        if "env" in run:
            del self["run"]["env"]

    def _parse_healthcheck(self, config: dict | None = None):
        if config:
            self["healthcheck"] = HealthCheck(config).as_dict()
        else:
            self["healthcheck"] = {}

    def _normalize_ports(self, default_proxy: str = "none"):
        if "port" not in self:
            self.port = {}
            return
        if not isinstance(self.port, dict):
            error("Site['port'] must be a dict")
        keys = list(self.port.keys())
        for key in keys:
            self.port[key]["name"] = key
        self.port = list(self.port.values())
        normalize_ports(self.port, default_proxy)

    def used_ports(self) -> set[int]:
        used = set()
        # when method is used, ports became a dict:
        for port in self.port.values():
            if not port:  # could be an empty {} ?
                continue
            host = port["host"]
            # normalization done: host is present and either 'auto' or an int
            if isinstance(host, int):
                used.add(host)
        return used

    def allocate_auto_ports(self, allocator: Callable):
        if not self.port:
            return
        # when method is used, ports became a dict:
        for port in self.port.values():
            if port["host"] == "auto":
                port["host_use"] = allocator()
            else:
                port["host_use"] = port["host"]

    def ports_as_docker_params(self) -> dict:
        cont_ports = {}
        for port in self.port.values():
            cont_ports[f"{port['container']}/{port['protocol']}"] = port["host_use"]
        return cont_ports

    def _normalize_volumes(self):
        if "volume" not in self:
            self.volume = []
            return
        if not isinstance(self.volume, list):
            error("Site['volume'] must be a list")
        # filter empty elements
        volume_list = [v for v in self.volume if v]
        self.volume = Volume.normalize_list(volume_list)

    def rebased_volumes_upon_package_conf(self, package_dict: dict) -> list:
        """warning: here, no update of self data"""
        base_list = package_dict.get("volume") or []
        return self._merge_volumes_lists(base_list, self.volume)

    def _merge_volumes_lists(
        self, base_list: list[dict], update_list: list[dict]
    ) -> list[dict]:
        # filter empty elements
        base = [v for v in base_list if v]
        if not base:
            # if volumes are not configured in the package nua-config, there
            # is no point to add volumes in the instance configuration
            return []
        # 1) merging instance site upon package config:
        #    unicity key here is 'target', to replace package target by instance
        #    definition
        # 2) at host level and between several instances, it should be taken care
        #    higher level to have different 'source' values on the host
        merge_dict = {vol["target"]: vol for vol in (base + update_list)}
        return list(merge_dict.values())

    def update_instance_from_site(self, resource_updates: dict):
        for key, value in resource_updates.items():
            # brutal replacement, TODO make special cases for volumes
            # less brutal:
            if key not in {"port", "run", "volume", "name", "assign"}:
                warning(f"maybe updating an unknown key in the configuration '{key}'")
            if key not in self:
                self[key] = value
                continue
            self._update_instance_from_site_deep(key, value)

    def _update_instance_from_site_deep(self, key: str, value):
        orig = self[key]
        if isinstance(orig, dict):
            if not isinstance(value, dict):
                error(
                    "Updated value in deploy config must be a dict.",
                    explanation=f"{orig=}\n{value=}",
                )
            orig.update(value)
            return
        if key == "volume":
            return self._update_instance_from_site_deep_volume(value)
        if key == "assign":
            return self._update_instance_from_site_deep_assign(value)
        # unknow, (or ports?) be brutal
        self[key] = value

    def _update_instance_from_site_deep_volume(self, value):
        if not isinstance(value, list):
            error(
                "Updated volumes in deploy config must be a list.",
                explanation=f"{value=}",
            )
        vol_dic = {}
        for orig_vol in self.volume:
            vol_dic[orig_vol["target"]] = orig_vol
        for update_vol in value:
            vol_dic[update_vol["target"]] = update_vol
        self.volume = list(vol_dic.values())

    def _update_instance_from_site_deep_assign(self, value):
        if not isinstance(value, list):
            error(
                "Updated assignment in deploy config must be a list.",
                explanation=f"{value=}",
            )
        assign_dic = {}
        for orig in self.assign:
            if "key" in orig:
                assign_dic[orig["key"]] = orig
        for update in value:
            if "key" in orig:
                assign_dic[orig["key"]] = update
        self.assign = list(assign_dic.values())

    def require_network(self) -> bool:
        """Heuristic to evaluate the need of docker private network.

        Basic: using a docker container as resource probably implies need of network.
        """
        if self.type == "docker":
            return True
        return False

    def environment_ports(self) -> dict:
        """Return exposed ports and resource host (container name) as env
        variables.

        To be used by remote container from same bridge network to
        connect to the resource container port.
        """
        run_env = {}
        for port in self.port.values():
            variable = f"NUA_{self.resource_name.upper()}_PORT_{port['container']}"
            value = str(port["host_use"])
            run_env[variable] = value
        variable = f"NUA_{self.resource_name.upper()}_HOST"
        run_env[variable] = self.container
        return run_env

    def add_requested_secrets(self, key: str):
        if verbosity(3):
            print(self)
            print("add_requested_secrets", key)
        self.requested_secrets.append(key)
        for resource in self.resources:
            resource.add_requested_secrets(key)
