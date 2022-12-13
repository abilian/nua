from copy import deepcopy
from pprint import pformat

from nua.lib.panic import error, warning
from nua.lib.tool.state import verbosity

from .domain_split import DomainSplit
from .port_normalization import normalize_ports, ports_as_dict
from .resource import Resource
from .utils import sanitized_name


class Site(Resource):
    MANDATORY_KEYS = ("image", "domain")

    def __init__(self, site_dict: dict):
        super().__init__(site_dict)
        self.type = "nua-site"

    def check_valid(self):
        self._check_mandatory()
        self._parse_run_env()
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
    def image_nua_config(self, image_nua_config: str):
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
    def nua_long_name(self) -> str:
        meta = self.image_nua_config["metadata"]
        release = meta.get("release", "")
        rel_tag = f"-{release}"
        if release:
            rel_tag = f"-{release}"
        else:
            rel_tag = ""
        if meta["id"].startswith("nua-"):
            nua_prefix = ""
        else:
            nua_prefix = "nua-"
        return f"{nua_prefix}{meta['id']}-{meta['version']}{rel_tag}"

    @property
    def container_name(self) -> str:
        suffix = DomainSplit(self.domain).containner_suffix()
        name_base = f"{self.nua_long_name}-{suffix}"
        return sanitized_name(name_base)

    def set_network_name(self):
        self.detect_required_network()
        if self.network_name:
            for resource in self.resources:
                resource.network_name = self.network_name

    def detect_required_network(self):
        """Evaluate the need of a bridge private network.

        If needed, stet a relevant network name.
        """
        self.network_name = ""
        if any(resource.require_network() for resource in self.resources):
            self.network_name = self.container_name
            if verbosity(4):
                print("detect_required_network() network_name =", self.network_name)

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

    def rebased_volumes_upon_nua_conf(self):
        """warning: here, no update of self data"""
        return self.rebased_volumes_upon_package_conf(self.image_nua_config)

    def rebase_ports_upon_nua_config(self):
        config_ports = deepcopy(self.image_nua_config.get("port", {}))
        if not isinstance(config_ports, dict):
            error("nua_config['port'] must be a dict")

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
        for resource in self.resources:
            resource.port = ports_as_dict(resource.port)
