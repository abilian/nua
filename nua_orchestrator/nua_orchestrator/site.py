from copy import deepcopy
from pprint import pformat

from .domain_split import DomainSplit
from .panic import error, warning
from .port_normalization import normalize_ports, ports_as_dict
from .resource import Resource
from .state import verbosity
from .utils import sanitized_name


class Site(Resource):
    MANDATORY_KEYS = ("image", "domain")

    def __init__(self, site_dict: dict):
        super().__init__(site_dict)
        self.type = "nua-site"

    def check_valid(self):
        self._check_mandatory()
        self._normalize_ports(default_proxy="auto")
        self._normalize_domain()

    @property
    def resources(self) -> list:
        return self.get("resources", [])

    @resources.setter
    def resources(self, resources: list):
        self["resources"] = resources

    @property
    def image_nua_config(self) -> dict:
        return self["image_nua_config"]

    @image_nua_config.setter
    def image_nua_config(self, image_nua_config: str):
        self["image_nua_config"] = image_nua_config

    @property
    def required_services(self) -> set:
        return self.get("required_services", set())

    @required_services.setter
    def required_services(self, required_services: set):
        self["required_services"] = required_services

    def _merged_instance_network_name(self) -> str:
        instance = self.image_nua_config.get("instance", {})
        network_name = instance.get("network") or ""
        if not network_name:
            return ""
        renamed = self.get("network") or ""
        network_name = renamed if renamed else network_name
        return sanitized_name(network_name)

    def set_network_name(self):
        self.network_name = self._merged_instance_network_name()
        if self.network_name:
            for resource in self.resources:
                resource.network_name = self.network_name

    def resource_per_name(self, name: str) -> Resource | None:
        for resource in self.resources:
            if resource.resource_name == name:
                return resource
        return None

    def merge_instance_to_resources(self):
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
                f"ignoring update for '{self.name}' resource, need a dict",
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

    def services_instance_updated(self) -> set:
        instance = self.image_nua_config.get("instance", {})
        instance.update({k: v for k, v in self.items() if not isinstance(v, dict)})
        services = instance.get("services") or []
        if isinstance(services, str):
            services = [services]
        if verbosity(3):
            print(f"Site services: {pformat(services)}")
        return set(services)

    def normalize_required_services(self, available_services: dict):
        services = self.services_instance_updated()
        for name, handler in available_services.items():
            for alias in handler.aliases():
                if alias in services:
                    services.discard(alias)
                    services.add(name)
        return services

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
                    f"ignoring resource declaration without {required_key}",
                    pformat(declaration),
                )
                return None
        # for now, only "docker" resources are implemented:
        if declaration["type"] != "docker":
            warning(
                f"ignoring resource of type {declaration['type'] }",
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

    def rebased_volumes_upon_nua_conf(self):
        """warning: here, no update of self data"""
        return self.rebased_volumes_upon_package_conf(self.image_nua_config)

    def rebase_ports_upon_nua_config(self):
        config_ports = deepcopy(self.image_nua_config.get("ports", []))
        if not isinstance(config_ports, list):
            error("nua_config['ports'] must be a list")
        normalize_ports(config_ports, default_proxy="auto")
        ports = ports_as_dict(config_ports)
        if verbosity(5):
            print(f"rebase_ports_upon_nua_config(): ports={pformat(ports)}")
        ports.update(self.ports)
        self.ports = ports
        for resource in self.resources:
            resource.ports = ports_as_dict(resource.ports)

    @property
    def nua_long_name(self) -> str:
        meta = self.image_nua_config["metadata"]
        release = meta.get("release", "")
        rel_tag = f"-{release}" if release else ""
        nua_prefix = "" if meta["id"].startswith("nua-") else "nua-"
        return f"{nua_prefix}{meta['id']}-{meta['version']}{rel_tag}"

    @property
    def container_name(self) -> str:
        suffix = DomainSplit(self.domain).containner_suffix()
        name_base = f"{self.nua_long_name}-{suffix}"
        return sanitized_name(name_base)
