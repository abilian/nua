import os
from collections.abc import Callable
from pathlib import Path

from nua.lib.panic import error, warning

from .port_normalization import normalize_ports, ports_as_dict
from .utils import sanitized_name
from .volume_normalization import normalize_volumes

NUA_PG_PWD_FILE = ".postgres_pwd"  # noqa S105
NUA_MARIADB_PWD_FILE = ".mariadb_pwd"  # noqa S105


class Resource(dict):
    MANDATORY_KEYS = ("image", "type")

    def __init__(self, declaration: dict):
        super().__init__(declaration)

    def check_valid(self):
        self._check_mandatory()
        self._parse_run_env()
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
    def container(self) -> str:
        return self.get("container", "")

    @container.setter
    def container(self, name: str):
        self["container"] = name

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
    def secrets(self) -> list[str]:
        return self.get("secrets", [])

    @secrets.setter
    def secrets(self, secrets_list: list | str):
        if secrets_list:
            if isinstance(secrets_list, str):
                secrets_list = [secrets_list]
            self["secrets"] = secrets_list
        else:
            self["secrets"] = []

    def set_ports_as_dict(self):
        """replace ports list by a dict with container port as key.

        (use str key because later conversion to json)
        """
        ports_dict = ports_as_dict(self.port)
        self.port = ports_dict

    def _check_mandatory(self):
        for key in self.MANDATORY_KEYS:
            if not self.get(key):
                error(f"Site or Resource configuration missing '{key}' key")

    def _parse_run_env(self):
        old_format = self.run_env
        run_env = self.get("run", {}).get("env", {})
        if not isinstance(run_env, dict):
            error("[run.env] must be a dict")
        old_format.update(run_env)
        self.run_env = old_format
        run = self.get("run", {})
        if "env" in run:
            del self["run"]["env"]

    def _normalize_ports(self, default_proxy: str = "none"):
        if "port" not in self:
            self.port = []
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
        self.volume = [v for v in self.volume if v]
        normalize_volumes(self.volume)

    # def update_volume_from_instance(self, instance_dict: dict) -> list:
    #     self.volume = self._merge_volumes_lists(instance_dict, reverse=True)

    def rebased_volumes_upon_package_conf(self, package_dict: dict) -> list:
        """warning: here, no update of self data"""
        return self._merge_volumes_lists(package_dict, reverse=False)

    def _merge_volumes_lists(self, other_dict: dict, reverse: bool) -> list:
        base = other_dict.get("volume") or []
        base = [v for v in base if v]
        if not base:
            # if volumes are not configured in the package nua-config, there
            # is no point to add vomlumes in the site configuration
            return []
        merge_dict = {}
        merge_list = base + self.volume
        if reverse:
            merge_list.reverse()
        for vol in merge_list:
            # 1) merging instance site / package config:
            #    unicity key here is 'target', to replace package target by instance
            #    definition
            # 2) at host level and between several instance, it should be taken care
            #    higher level to have different 'source' vales on the host
            merge_dict[vol["target"]] = vol
        return list(merge_dict.values())

    def update_instance_from_site(self, resource_updates: dict):
        # print("update_instance_from_site()")
        # print(pformat(resource_updates))
        # print("--------")
        # print(pformat(self))
        for key, value in resource_updates.items():
            # brutal replacement, TODO make special cases for volumes
            # less brutal:
            if key not in {"port", "run", "run_env", "volume", "name"}:
                warning(
                    "maybe updating an unknown key in " f"the configuration '{key}'"
                )
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

    @staticmethod
    def _postgres_pwd() -> str:
        """Return the 'postgres' user DB password.

          - When used in container context, the env variable NUA_POSTGRES_PASSWORD should
            contain the password.
          - When used in nua-orchestrator context, read the password from local file.

        For orchestrator context, assuming this function can only be used *after*
        password was generated (or its another bug).

        Rem.: No cache. Rarely used function and pwd can be changed.
        """
        pwd = os.environ.get("NUA_POSTGRES_PASSWORD")
        if pwd:
            return pwd
        file_path = Path(os.path.expanduser("~nua")) / NUA_PG_PWD_FILE
        return file_path.read_text(encoding="utf8").strip()

    @staticmethod
    def _mariadb_pwd() -> str:
        """Return the 'root' user DB password of mariadb.

          - When used in container context, the env variable NUA_MARIADB_PASSWORD should
            contain the password.
          - When used in nua-orchestrator context, read the password from local file.

        For orchestrator context, assuming this function can only be used *after* password
        was generated (or its another bug).

        Rem.: No cache. Rarely used function and pwd can be changed.
        """
        pwd = os.environ.get("NUA_MARIADB_PASSWORD")
        if pwd:
            return pwd
        file_path = Path(os.path.expanduser("~nua")) / NUA_MARIADB_PWD_FILE
        return file_path.read_text(encoding="utf8").strip()

    def read_secrets(self) -> dict:
        if not self.secrets:
            return {}
        secrets_env = {}
        if "POSTGRES_PASSWORD" in self.secrets:
            secrets_env["POSTGRES_PASSWORD"] = self._postgres_pwd()
        if "MARIADB_PASSWORD" in self.secrets:
            secrets_env["MARIADB_PASSWORD"] = self._mariadb_pwd()
        return secrets_env
