from __future__ import annotations

from collections.abc import Callable
from pprint import pformat

from nua.lib.panic import abort, vprint, warning
from nua.lib.tool.state import verbosity

from .backup.backup_engine import backup_resource, backup_volume
from .backup.backup_report import global_backup_report
from .healthcheck import HealthCheck
from .port_normalization import normalize_ports, ports_as_dict
from .register_plugins import (
    is_assignable_plugin,
    is_db_plugins,
    is_docker_plugin,
    is_network_plugin,
    load_plugin_function,
)
from .utils import sanitized_name
from .volume import Volume

CONTAINER_TYPE = {"docker"}
DOCKER_TYPE = {"docker"}
ASSIGNABLE_TYPE = CONTAINER_TYPE
NETWORKED_TYPE = CONTAINER_TYPE


class Resource(dict):
    def __init__(self, declaration: dict):
        super().__init__(declaration)
        if "requested_secrets" not in self:
            self.requested_secrets = []

    @classmethod
    def from_dict(cls, resource_dict: dict) -> Resource:
        resource = cls({})
        for key, val in resource_dict.items():
            resource[key] = val
        resource["port"] = resource.get("port") or {}
        return resource

    def check_valid(self):
        self._check_mandatory()
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
        return self.get("image") or ""

    @image.setter
    def image(self, image: str):
        self["image"] = image

    @property
    def version(self) -> str:
        return self.get("version") or ">0"

    @version.setter
    def version(self, version: str):
        self["version"] = version

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
    def assign_priority(self) -> int:
        return self.get("assign_priority", 10)

    @assign_priority.setter
    def assign_priority(self, assign_priority: int):
        self["assign_priority"] = assign_priority

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
    def volume_declaration(self) -> list:
        """Docker volume declred on a non-container resource.

        Thus this volume need to be started by the upper site.
        """
        return self.get("volume_declaration", [])

    @volume_declaration.setter
    def volume_declaration(self, volume_declaration: list):
        self["volume_declaration"] = volume_declaration

    @property
    def hostname(self) -> str:
        return self.get("hostname", "")

    @hostname.setter
    def hostname(self, hostname: str):
        self["hostname"] = hostname

    @property
    def docker(self) -> dict:
        return self.get("docker", {})

    @docker.setter
    def docker(self, docker: dict):
        self["docker"] = docker

    @property
    def run_params(self) -> dict:
        return self.get("run_params", {})

    @run_params.setter
    def run_params(self, run_params: dict):
        self["run_params"] = run_params

    @property
    def env(self) -> dict:
        return self.get("env", {})

    @env.setter
    def env(self, env: dict):
        self["env"] = env

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
    def container_name(self) -> str:
        return self.get("container_name", "")

    @container_name.setter
    def container_name(self, container_name: str):
        self["container_name"] = container_name

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
    def healthcheck(self) -> dict:
        if "healthcheck" not in self:
            self["healthcheck"] = {}
        return self["healthcheck"]

    @healthcheck.setter
    def healthcheck(self, healthcheck: dict):
        self["healthcheck"] = healthcheck

    def is_assignable(self) -> bool:
        """Resource type allow env persistent parameters ("assign" key word).

        Persistent data is stored at site level (not resource level).
        """
        return self.type in ASSIGNABLE_TYPE or is_assignable_plugin(self.type)

    def set_ports_as_dict(self):
        """Replace ports list by a dict with container port as key.

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
            abort(f"Site or Resource configuration missing '{key}' key")

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
            abort("Site['port'] must be a dict")
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
            abort("Site['volume'] must be a list")
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
            if key not in {"port", "env", "docker", "volume", "name", "assign"}:
                warning(f"maybe updating an unknown key in the configuration '{key}'")
            if key not in self:
                self[key] = value
                continue
            self._update_instance_from_site_deep(key, value)

    def _update_instance_from_site_deep(self, key: str, value):
        orig = self[key]
        if isinstance(orig, dict):
            if not isinstance(value, dict):
                abort(
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
            abort(
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
            abort(
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

    def requires_network(self) -> bool:
        """Heuristic to evaluate the need of docker private network.

        Basic: using a docker container as resource probably implies need of network.
        """
        return self.type in NETWORKED_TYPE or is_network_plugin(self.type)

    def is_docker_type(self) -> bool:
        """Test if resource has a docker-like type."""
        return self.type in DOCKER_TYPE or is_docker_plugin(self.type)

    def environment_ports(self) -> dict:
        """Return exposed ports and resource host (container name) as env
        variables.

        To be used by remote container from same bridge network to
        connect to the resource container port.
        """
        env = {}
        for port in self.port.values():
            variable = f"NUA_{self.resource_name.upper()}_PORT_{port['container']}"
            value = str(port["host_use"])
            env[variable] = value
        return env

    def add_requested_secrets(self, key: str):
        with verbosity(3):
            vprint(self)
            vprint("add_requested_secrets", key)
        self.requested_secrets.append(key)
        for resource in self.resources:
            resource.add_requested_secrets(key)

    def do_full_backup(self) -> str:
        """Execute a full backup.

         backup order:
        1 - resources
        2 - site
        for each:
        a) backup tag of each volume
        b) backup tag of main resource
        """
        reports = []
        for resource in self.resources:
            reports.extend(resource.do_backup())
        reports.extend(self.do_backup())
        return global_backup_report(reports)

    def do_backup(self) -> list:
        reports = []
        for volume_dict in self.volume:
            volume = Volume.from_dict(volume_dict)
            reports.append(backup_volume(volume))
        reports.append(backup_resource(self))
        return reports

    def setup_db(self):
        if not is_db_plugins(self.type):
            return
        if setup_fct := load_plugin_function(self.type, "setup_db"):
            setup_fct(self)
            with verbosity(2):
                vprint(f"setup_db() for resource '{self.resource_name}': {self.type}")
            with verbosity(3):
                vprint(pformat(self.env))

    def configure_db(self):
        with verbosity(4):
            vprint(f"configure_db: {self.type}")
        if not is_db_plugins(self.type):
            with verbosity(4):
                vprint(f"not a DB: {self.type}")
            return
        if configure_fct := load_plugin_function(self.type, "configure_db"):
            with verbosity(4):
                vprint(f"configure_fct: {configure_fct}")
            configure_fct(self)
            with verbosity(2):
                vprint(f"configure_db() resource '{self.resource_name}': {self.type}")
            with verbosity(3):
                vprint(pformat(self))
