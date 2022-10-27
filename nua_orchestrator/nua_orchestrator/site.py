from copy import deepcopy
from pprint import pformat
from string import ascii_letters, digits

from .domain_split import DomainSplit
from .port_normalization import normalize_ports, ports_as_dict
from .resource import Resource
from .state import verbosity

ALLOW_DOCKER_NAME = set(ascii_letters + digits + "-_.")


class Site(Resource):
    MANDATORY_KEYS = ("image", "domain")

    def __init__(self, site_dict: dict):
        super().__init__(site_dict)
        self.type = "nua-site"

    def check_valid(self):
        self._check_mandatory()
        self._normalize_ports()
        self._normalize_domain()

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

    def _normalize_domain(self):
        dom = DomainSplit(self.domain)
        self.domain = dom.full_path()

    def rebased_volumes_upon_nua_conf(self):
        """warning: here, no update of self data"""
        return self.rebased_volumes_upon_package_conf(self.image_nua_config)

    def rebase_ports_upon_nua_config(self):
        config_ports = deepcopy(self.image_nua_config.get("ports", []))
        if not isinstance(config_ports, list):
            raise ValueError("nua_config['ports'] must be a list")
        normalize_ports(config_ports)
        ports = ports_as_dict(config_ports)
        if verbosity(5):
            print(f"rebase_ports_upon_nua_config(): ports={pformat(ports)}")
        ports.update(self.ports)
        self.ports = ports

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
        return "".join([x for x in name_base if x in ALLOW_DOCKER_NAME])
