from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from pprint import pformat

from nua.lib.panic import abort, warning
from nua.lib.tool.state import verbosity
from nua.runtime.nua_tag import nua_tag_string

from .domain_split import DomainSplit
from .persistent import Persistent
from .port_normalization import normalize_ports, ports_as_dict
from .resource import Resource
from .search_cmd import search_nua
from .utils import sanitized_name
from .volume import Volume


class Site(Resource):
    MANDATORY_KEYS = ("image", "domain")

    def __init__(self, site_dict: dict):
        super().__init__(site_dict)
        self.type = "nua-site"

    @classmethod
    def from_dict(cls, site_dict: dict) -> Site:
        site = cls({})
        resources = []
        for res in site_dict.get("resources", []):
            resources.append(Resource.from_dict(res))
        for key, val in site_dict.items():
            if key == "resources":
                continue
            site[key] = val
        site["resources"] = resources
        site["port"] = site.get("port") or {}
        return site

    def check_valid(self):
        self._check_mandatory()
        self._normalize_ports(default_proxy="auto")
        self._normalize_domain()

    @property
    def resources(self) -> list:
        """List of sub resources of the Site object.

        Warning: only Site class has an actual use of 'resources'.
        The sub class Resource will always provide an *empty* list
        """
        return self.get("resources", [])

    @resources.setter
    def resources(self, resources: list):
        self["resources"] = resources

    @property
    def image_nua_config(self) -> dict:
        return self["image_nua_config"]

    @image_nua_config.setter
    def image_nua_config(self, image_nua_config: dict):
        self["image_nua_config"] = image_nua_config

    @property
    def assign(self) -> list:
        return self.image_nua_config.get("assign", [])

    @assign.setter
    def assign(self, assign_list: list):
        self.image_nua_config["assign"] = assign_list

    @property
    def local_services(self) -> list:
        return [
            resource.service for resource in self.resources if resource.type == "local"
        ]

    @property
    def app_id(self) -> str:
        return self.image_nua_config["metadata"]["id"]
        # if app_id.startswith("nua-"):
        #     app_id = app_id[4:]
        # return app_id

    @property
    def nua_tag(self) -> str:
        return nua_tag_string(self.image_nua_config["metadata"])

    @property
    def container_name(self) -> str:
        # override the method of Resource
        suffix = DomainSplit(self.domain).container_suffix()
        name = sanitized_name(f"{self.nua_tag}-{suffix}")
        self["container_name"] = name
        return name

    def persistent(self, name: str) -> Persistent:
        """Return Persistent instance for resource of name 'name'.

        Use name = '' for main site.
        """
        if "persistent" not in self:
            self["persistent"] = {}
        content = self["persistent"].get(name, {})
        return Persistent.from_name_dict(name, content)

    def set_persistent(self, persistent: Persistent):
        if "persistent" not in self:
            self["persistent"] = {}
        self["persistent"].update(persistent.as_dict())

    def persistent_full_dict(self) -> dict:
        if "persistent" not in self:
            self["persistent"] = {}
        return self["persistent"]

    def set_persistent_full_dict(self, persist_dict: dict):
        self["persistent"] = persist_dict

    def parse_healthcheck(self):
        self._parse_healthcheck(self.image_nua_config.get("healthcheck", {}))

    def set_volumes_names(self):
        suffix = DomainSplit(self.domain).container_suffix()
        self.volume = [Volume.update_name_dict(v, suffix) for v in self.volume]
        for resource in self.resources:
            resource.volume = [
                Volume.update_name_dict(v, suffix) for v in resource.volume
            ]

    @property
    def registry_path(self) -> str:
        return self.get("registry_path") or ""

    @registry_path.setter
    def registry_path(self, registry_path: str | Path):
        self["registry_path"] = str(registry_path)

    def set_network_name(self):
        """Evaluate the need of a bridge private network.

        If needed, set a relevant network name.
        """
        self.network_name = ""
        if any(resource.requires_network() for resource in self.resources):
            self.network_name = self.container_name
            for resource in self.resources:
                resource.network_name = self.network_name
            if verbosity(4):
                print("detect_required_network() network_name =", self.network_name)

    def resource_per_name(self, name: str) -> Resource | None:
        for resource in self.resources:
            if resource.resource_name == name:
                return resource
        return None

    def merge_instance_to_resources(self):
        self.rebase_volumes_upon_nua_conf()
        resource_declarations = self.get("resource", [])
        if not resource_declarations:
            return
        for resource_updates in resource_declarations:
            self._merge_resource_updates_to_resource(resource_updates)

    def _merge_resource_updates_to_resource(self, resource_updates):
        if not resource_updates:
            # no redefinition of any configuration of the resource
            return
        if not isinstance(resource_updates, dict):
            warning(
                f"ignoring update for '{self.domain}' resources, need a dict",
                explanation=pformat(resource_updates),
            )
            return
        resource_name = resource_updates.get("name")
        if not resource_name or not isinstance(resource_name, str):
            warning(
                "ignoring resource update without name",
                pformat(resource_updates),
            )
            return
        resource = self.resource_per_name(resource_name)
        if not resource:
            warning(f"ignoring resource update, unknown resource '{resource_name}'")
        resource.update_instance_from_site(resource_updates)

    def parse_resources(self):
        resources = [
            self._parse_resource(resource_declaration)
            for resource_declaration in self.image_nua_config.get("resource", [])
        ]
        resources = [res for res in resources if res]
        if verbosity(3):
            print(f"Image resources: {pformat(resources)}")
        self.resources = resources

    def _parse_resource(self, declaration: dict) -> Resource | None:
        for required_key in ("name", "type"):
            value = declaration.get(required_key)
            if not value or not isinstance(value, str):
                warning(
                    f"ignoring resource declaration without '{required_key}'",
                    pformat(declaration),
                )
                return None
        resource = Resource(declaration)
        resource.resource_name = declaration["name"]
        resource.check_valid()
        return resource

    def _normalize_domain(self):
        dom = DomainSplit(self.domain)
        self.domain = dom.full_path()

    # CHANGE: now volumes updated in site configuration, so
    # different strategy for store.py
    # def rebased_volumes_upon_nua_conf(self):
    #     """warning: here, no update of self data"""
    #     return self.rebased_volumes_upon_package_conf(self.image_nua_config)

    def rebase_volumes_upon_nua_conf(self):
        self.volume = self.rebased_volumes_upon_package_conf(self.image_nua_config)

    def rebase_ports_upon_nua_config(self):
        config_ports = deepcopy(self.image_nua_config.get("port", {}))
        if not isinstance(config_ports, dict):
            abort("nua_config['port'] must be a dict")

        keys = list(config_ports.keys())
        for key in keys:
            config_ports[key]["name"] = key
        config_ports = list(config_ports.values())
        normalize_ports(config_ports, default_proxy="auto")
        ports = ports_as_dict(config_ports)
        if verbosity(4):
            print(f"rebase_ports_upon_nua_config(): ports={pformat(ports)}")
        ports.update(self.port)
        self.port = ports

    def find_registry_path(self, cached: bool = False) -> bool:
        # list of images sorted by version:
        if cached and self.registry_path:
            return True
        results = self._search_nua_registry()
        if results:
            # results are sorted by version, take higher:
            self.registry_path = results[-1]
        else:
            self.registry_path = ""
        return bool(self.registry_path)

    def _search_nua_registry(self) -> list:
        if self.type not in {"nua-site", "docker"}:
            raise ValueError(f"Unsupported type of container '{self.type}'")
        return search_nua(self.image)

    def set_resources_names(
        self,
    ):
        """Set first container names of resources to permit early host
        assignment to variables.

        Site.container_name is always available.
        """
        for resource in self.resources:
            if resource.is_docker_type():
                name = f"{self.container_name}-{resource.base_name}"
                resource.container_name = name
                # docker resources are only visible from bridge network, so use
                # the container name as hostname
                resource.hostname = name
