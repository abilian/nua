from pprint import pformat

from .domain_split import DomainSplit
from .resource import Resource
from .state import verbosity


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
