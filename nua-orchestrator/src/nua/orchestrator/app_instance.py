from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from pprint import pformat

from nua.agent.nua_config import hyphen_get
from nua.agent.nua_tag import nua_tag_string
from nua.lib.panic import Abort, info, vprint, warning
from nua.lib.tool.state import verbosity

from .db.model.instance import STOPPED
from .domain_split import DomainSplit
from .persistent import Persistent
from .port_normalization import (
    normalize_ports_list,
    ports_as_list,
    rebase_ports_on_defaults,
)
from .resource import Resource
from .resource_deps import ResourceDeps
from .search_cmd import search_nua
from .utils import sanitized_name
from .volume import Volume


class AppInstance(Resource):
    MANDATORY_KEYS = ("image", "domain")

    def __init__(self, app_instance_dict: dict):
        super().__init__(app_instance_dict)
        self.type = "nua-site"

    @classmethod
    def from_dict(cls, app_instance_dict: dict) -> AppInstance:
        app_instance = cls({})
        resources = []
        for res in app_instance_dict.get("resources", []):
            resources.append(Resource.from_dict(res))
        for key, val in app_instance_dict.items():
            if key == "resources":
                continue
            app_instance[key] = val
        app_instance["resources"] = resources
        app_instance["port"] = app_instance.get("port") or {}
        return app_instance

    def check_valid(self):
        self._check_mandatory()
        self._nomalize_env_values()
        self._normalize_ports()
        self._normalize_domain()
        self._set_instance_name()

    @property
    def resources(self) -> list:
        """List of sub resources of the AppInstance object.

        Warning: only AppInstance class has an actual use of 'resources'.
        The subclass Resource will always provide an *empty* list
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
    def instance_name_internal(self) -> str:
        return self["instance_name_internal"]

    @property
    def instance_name_user(self) -> str:
        return self["instance_name_user"]

    @property
    def top_domain(self) -> str:
        return self["top_domain"]

    @top_domain.setter
    def top_domain(self, top_domain: str):
        self["top_domain"] = top_domain

    @property
    def local_services(self) -> list:
        return [
            resource.service for resource in self.resources if resource.type == "local"
        ]

    @property
    def app_id(self) -> str:
        return self.image_nua_config["metadata"]["id"]

    @property
    def image_short(self) -> str:
        """Return short app id from deployment 'image' value.

        Used early: at that moment the Docker image and actual
        image/nua_config are not available.

        Remove 'nua-' prefix and version):  "nua-hedgedoc" ->
        "hedgedoc".
        """
        image = self.image.strip()
        if image.startswith("nua-"):
            image = image[4:]
        return image.split(":")[0]

    @property
    def nua_tag(self) -> str:
        """Return long tag string with version and release.

        "hedgedoc" -> "nua-hedgedoc:1.9.7-3"
        """
        return nua_tag_string(self.image_nua_config["metadata"])

    @property
    def nua_dash_name(self) -> str:
        return self.nua_tag.replace(":", "-")

    @property
    def container_name(self) -> str:
        # override the method of Resource
        suffix = DomainSplit(self.domain).container_suffix()
        name = sanitized_name(f"{self.nua_dash_name}-{suffix}")
        self["container_name"] = name
        return name

    @property
    def running_status(self) -> str:
        return self.get("running_status", STOPPED)

    @running_status.setter
    def running_status(self, status: str):
        self["running_status"] = status

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
            with verbosity(4):
                vprint("detect_required_network() network_name =", self.network_name)

    def resource_per_name(self, name: str) -> Resource | None:
        for resource in self.resources:
            if resource.resource_name == name:
                return resource
        return None

    def merge_instance_to_resources(self):
        self.rebase_env_upon_nua_conf()
        self.rebase_volumes_upon_nua_conf()
        self.rebase_ports_upon_nua_config()
        resource_declarations = self.get("resource", [])
        if not resource_declarations:
            return
        for resource_updates in resource_declarations:
            self._merge_resource_updates_to_resource(resource_updates)

    def rebase_env_upon_nua_conf(self):
        """Merge AppInstance declared env at deploy time upon base declaration
        of nua-config."""
        base_env = deepcopy(self.image_nua_config.get("env", {}))
        base_env.update(self.env)
        self.env = base_env

    def order_resources_dependencies(self) -> list[Resource]:
        """Order of evaluations for variables.

        - main AppInstance variable assignment (including hostname of resources)
        - late evaluation (hostnames)
        And check for circular dependencies of resources.
        """
        resource_deps = ResourceDeps()
        for resource in self.resources:
            resource_deps.add_resource(resource)
        resource_deps.add_resource(self)
        return resource_deps.solve()

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
        resource.update_from_site_declaration(resource_updates)

    def parse_resources(self):
        resources = [
            self._parse_resource(resource_declaration)
            for resource_declaration in self.image_nua_config.get("resource", [])
        ]
        resources = [res for res in resources if res]
        with verbosity(3):
            vprint(f"Image resources: {pformat(resources)}")
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
        self.top_domain = dom.top_domain()

    def _set_instance_name(self):
        name = hyphen_get(self, "instance-name") or ""
        if not "_".join(name.split()):
            name = self.default_instance_name()
            with verbosity(0):
                info(f"Instance name not provided, using default: '{name}'")
        self.set_instance_name(name)

    def set_instance_name(self, name: str):
        name_internal = "_".join(name.split())
        if not name_internal:
            raise ValueError("Empty name instance is not allowed")
        self["instance_name_internal"] = name_internal
        self["instance_name_user"] = name.strip()

    def rebase_volumes_upon_nua_conf(self):
        self.volume = self.rebased_volumes_upon_package_conf(self.image_nua_config)

    def rebase_ports_upon_nua_config(self):
        nua_config_ports = deepcopy(self.image_nua_config.get("port", {}))
        if not isinstance(nua_config_ports, dict):
            raise Abort("nua_config['port'] must be a dict")

        base_ports = normalize_ports_list(ports_as_list(nua_config_ports))
        self.port_list = rebase_ports_on_defaults(base_ports, self.port_list)
        with verbosity(4):
            vprint(f"rebase_ports_upon_nua_config(): ports={pformat(self.port_list)}")

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

    def set_resources_names(self):
        """Set first container names of resources to permit early host
        assignment to variables.

        AppInstance.container_name is always available.
        """
        for resource in self.resources:
            if resource.is_docker_type():
                name = f"{self.container_name}-{resource.base_name}"
                resource.container_name = name
                # docker resources are only visible from bridge network, so use
                # the container name as hostname
                resource.hostname = name

    def default_instance_name(self):
        """Return a name based on app id and domain.

        To use when the user does not provide an app name or as default
        value.
        """
        return f"{self.image_short}-{self.domain}"
