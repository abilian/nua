from __future__ import annotations

from collections.abc import Callable
from copy import deepcopy
from typing import Any

from nua.lib.normalization import normalize_env_values, normalize_ports, ports_as_list
from nua.lib.nua_config import force_list
from nua.lib.panic import Abort, vprint, warning
from nua.lib.tool.state import verbosity

from .healthcheck import HealthCheck
from .port_utils import ports_as_docker_parameters, ports_assigned
from .utils import sanitized_name
from .volume import Volume

CONTAINER_TYPE = {"docker"}
DOCKER_TYPE = {"docker"}
ASSIGNABLE_TYPE = CONTAINER_TYPE
NETWORKED_TYPE = CONTAINER_TYPE


class Provider(dict):
    def __init__(self, provider_config: dict):
        super().__init__(provider_config)
        if "requested_secrets" not in self:
            self.requested_secrets = []
        # debug backup print("provider_decl", declaration)

    @classmethod
    def from_dict(cls, provider_dict: dict) -> Provider:
        provider = cls({})
        for key, val in provider_dict.items():
            provider[key] = val
        provider["port"] = provider.get("port") or {}
        return provider

    def check_valid(self):
        self._check_mandatory()
        self._normalize_env_values()
        self._normalize_ports()
        self._normalize_volumes()

    @property
    def providers(self) -> list:
        """List of sub providers of the object.

        Warning: only AppInstance upper class has an actual use of 'providers'.
        This subclass Provider will always provide an *empty* list.
        """
        return []

    @providers.setter
    def providers(self, _providers: list):
        pass

    @property
    def label_id(self) -> str:
        """Sanitized version of the app label.

        For providers, label_id is the label_id of the main app.
        """
        if "label_id" not in self:
            self["label_id"] = ""
        return self["label_id"]

    @label_id.setter
    def label_id(self, label_id: str) -> None:
        self["label_id"] = label_id

    @property
    def type(self) -> str:
        return self["type"]

    @type.setter
    def type(self, tpe: str):
        self["type"] = tpe

    @property
    def module_name(self) -> str:
        return self.get("module_name", "")

    @module_name.setter
    def module_name(self, module_name: str):
        self["module_name"] = module_name

    @property
    def name(self) -> str:
        return self["name"]

    @name.setter
    def name(self, name: str):
        self["name"] = name

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
    def domain(self) -> str:
        return self.get("domain", "")

    @domain.setter
    def domain(self, domain: str):
        self["domain"] = domain

    @property
    def domain_realm(self) -> str:
        if len(self.domain.split(".")) < 3:
            return self.domain
        return self.domain.split(".", 1)[-1]

    @property
    def nua_config(self) -> dict[str, Any]:
        """Return the image original nua-config dict."""
        return self.get("image_nua_config") or {}

    @property
    def config_build(self) -> dict[str, Any]:
        """Return the image original nua-config 'build' section"""
        return self.nua_config.get("build") or {}

    @property
    def config_run(self) -> dict[str, Any]:
        """Return the image original nua-config 'run' section"""
        return self.nua_config.get("run") or {}

    @property
    def env(self) -> dict:
        return self.get("env") or {}

    @env.setter
    def env(self, env: dict):
        self["env"] = env

    def base_image(self):
        image = ""
        if self.type == "docker-image":
            build = self.get("build") or {}
            image = build.get("base-image") or ""
            if not image:
                image = self.config_build.get("base-image") or ""
        return image

    @property
    def port(self) -> list | dict:
        return self["port"]

    @port.setter
    def port(self, ports: list | dict):
        self["port"] = ports

    @property
    def port_list(self) -> list:
        return self.get("port_list", [])

    @port_list.setter
    def port_list(self, port_list: list):
        self["port_list"] = port_list

    @property
    def volumes(self) -> list:
        return self.get("volume") or []

    @volumes.setter
    def volumes(self, volumes: list):
        self["volume"] = volumes

    @property
    def backup(self) -> dict[str, Any]:
        return self.get("backup", None)

    @backup.setter
    def backup(self, backup: dict[str, Any]):
        self["backup"] = backup

    @property
    def volume_declaration(self) -> list:
        """Docker volume declared on a non-container provider.

        Thus, this volume needs to be started by the upper site.
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
        return self.get("docker") or {}

    @docker.setter
    def docker(self, docker: dict):
        self["docker"] = docker

    @property
    def post_run(self) -> list[str]:
        """Return the image original nua-config 'run/post-run' value"""
        return force_list(self.config_run.get("post-run") or "")

    @property
    def post_run_status(self) -> str:
        """Return the image original nua-config 'run/post-run-status' value"""
        return self.config_run.get("post-run-status") or ""

    @property
    def run_params(self) -> dict:
        return self.get("run_params", {})

    @run_params.setter
    def run_params(self, run_params: dict):
        self["run_params"] = run_params

    @property
    def image_base_name(self) -> str:
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

    def set_container_name(self) -> None:
        base = f"{self.label_id}-{self.provider_name}"
        if self.is_docker_type():
            name = f"{base}-{self.image_base_name}"
        else:
            name = base
        self.container_name = name
        # docker providers are only visible from bridge network, so use
        # the container name as hostname
        self.hostname = name

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
    def provider_name(self) -> str:
        return self.get("provider_name", "")

    @provider_name.setter
    def provider_name(self, provider_name: str):
        self["provider_name"] = provider_name

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

    @property
    def meta_packages_requirements(self) -> list:
        return force_list(self.get("meta_packages_requirements") or "")

    @meta_packages_requirements.setter
    def meta_packages_requirements(self, meta_packages_requirements: list | None):
        if meta_packages_requirements:
            self["meta_packages_requirements"] = meta_packages_requirements
        else:
            self["meta_packages_requirements"] = []

    def _check_mandatory(self):
        self._check_missing("type")
        if self["type"] == "local":
            self._check_missing("service")
        elif self["type"] == "docker":
            self._check_missing("image")

    def _check_missing(self, key: str):
        if key not in self or not str(self[key]).strip():
            raise Abort(f"AppInstance or Provider configuration missing '{key}' key")

    def _parse_healthcheck(self, config: dict | None = None):
        if config:
            self["healthcheck"] = HealthCheck(config).as_dict()
        else:
            self["healthcheck"] = {}

    def _parse_backup(self, config: dict | None = None):
        if config:
            self.backup = config
        else:
            self.backup = {}

    def _normalize_env_values(self):
        if "env" not in self or not self.env:
            self.env = {}
        self.env = normalize_env_values(self.env)

    def _normalize_ports(self):
        if "port" not in self or not self.port:
            self.port = {}
            return

        if not isinstance(self.port, dict):
            raise Abort("AppInstance['port'] must be a dict")

        self.port_list = normalize_ports(ports_as_list(self.port))

    def used_ports(self) -> set[int]:
        return ports_assigned(self.port_list)

    def allocate_auto_ports(self, allocator: Callable):
        for port in self.port_list:
            if port["host"] is None:
                port["host_use"] = allocator()
            else:
                port["host_use"] = port["host"]

    def ports_as_docker_params(self) -> dict:
        return ports_as_docker_parameters(self.port_list)

    def _normalize_volumes(self):
        if "volume" not in self or not self.volumes:
            self.volumes = []
        if not isinstance(self.volumes, list):
            raise Abort("AppInstance['volume'] must be a list")
        # filter empty elements
        volume_list = [v for v in self.volumes if v]
        self.volumes = Volume.normalize_list(volume_list)

    def rebased_volumes_upon_package_conf(self, config_dict: dict) -> list:
        """warning: here, no update of self data"""
        base_list = config_dict.get("volume") or []
        base_list = [vol for vol in base_list if vol]
        if not base_list:
            # if volumes are not configured in the package nua-config, there
            # is no point to add volumes in the instance configuration
            return []
        # 1) merging instance site upon package config:
        #    unicity key here is 'target', to replace package target by instance
        #    definition
        # 2) at host level and between several instances, it should be taken care
        #    higher level to have different 'source' values on the host
        merge_dict = {vol["target"]: vol for vol in (base_list + self.volumes)}
        return list(merge_dict.values())

    def update_from_site_declaration(self, provider_updates: dict[str, Any]):
        for key, value in provider_updates.items():
            # brutal replacement, TODO make special cases for volumes
            # less brutal:
            if key not in {"port", "env", "docker", "volume", "name"}:
                warning(f"maybe updating an unknown key in the configuration '{key}'")
            if key not in self:
                self[key] = value
                continue
            self._update_from_site_declaration_case(key, value)

    def _update_from_site_declaration_case(self, key: str, value: Any):
        orig = self[key]
        if isinstance(orig, dict):
            if not isinstance(value, dict):
                raise Abort(
                    "Updated value in deploy config must be a dict.",
                    explanation=f"{orig=}\n{value=}",
                )
            orig.update(value)
            return
        if key == "volume":
            return self._update_from_site_declaration_volume(value)
        if key == "env":
            self._update_from_site_declaration_env(value)
        # unknown, (or ports?) be brutal
        self[key] = value

    def _update_from_site_declaration_volume(self, value: Any):
        if not isinstance(value, list):
            raise Abort(
                "Updated volumes in deploy config must be a list.",
                explanation=f"{value=}",
            )

        vol_dic = {}
        for orig_vol in self.volumes:
            vol_dic[orig_vol["target"]] = orig_vol
        for update_vol in value:
            vol_dic[update_vol["target"]] = update_vol
        self.volumes = list(vol_dic.values())

    def _update_from_site_declaration_env(self, env_update_dict: Any):
        """For Provider only, make 'env' dict from AppInstance declaration and
        base  delcaration in nua-config."""
        if not isinstance(env_update_dict, dict):
            raise Abort(
                "Updated 'env' in deploy config must be a dict.",
                explanation=f"{env_update_dict=}",
            )

        base_env = deepcopy(self.env)
        base_env.update(env_update_dict)
        self.env = deepcopy(base_env)

    def requires_network(self) -> bool:
        """Heuristic to evaluate the need of docker private network.

        Basic: using a docker container as provider probably implies need of network.
        """
        return self.is_docker_type() or self.get("network", False)

    def is_docker_type(self) -> bool:
        """Test if provider has a docker-like type."""
        return self.type == "docker-image"

    def environment_ports(self) -> dict:
        """Return exposed ports and provider host (container name) as env
        variables.

        To be used by remote container from same bridge network to
        connect to the provider container port.
        """
        env = {}
        for port in self.port_list:
            variable = f"NUA_{self.provider_name.upper()}_PORT_{port['container']}"
            value = str(port["host_use"])
            env[variable] = value
        return env

    def add_requested_secrets(self, key: str):
        with verbosity(3):
            vprint(self)
            vprint("add_requested_secrets", key)
        self.requested_secrets.append(key)
        for provider in self.providers:
            provider.add_requested_secrets(key)
