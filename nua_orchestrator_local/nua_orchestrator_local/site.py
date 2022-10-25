from pprint import pformat

from .domain_split import DomainSplit
from .port_normalization import normalize_ports, ports_as_dict
from .state import verbosity


class Site(dict):
    def __init__(self, site_dict: dict):
        super().__init__(site_dict)

    def check_valid(self):
        self._check_required()
        self._normalize_ports()
        self._normalize_domain()

    @property
    def ports(self) -> list | dict:
        return self["ports"]

    @ports.setter
    def ports(self, ports: list | dict):
        self["ports"] = ports

    @property
    def domain(self) -> str:
        return self["domain"]

    @domain.setter
    def domain(self, domain: str):
        self["domain"] = domain

    @property
    def image(self) -> str:
        return self["image"]

    @image.setter
    def image(self, image: str):
        self["image"] = image

    @property
    def hostname(self) -> str:
        return self.get("hostname", "")

    @hostname.setter
    def hostname(self, hostname: str):
        self["hostname"] = hostname

    @property
    def image_nua_config(self) -> dict:
        return self["image_nua_config"]

    @image_nua_config.setter
    def image_nua_config(self, image_nua_config: str):
        self["image_nua_config"] = image_nua_config

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
    def required_services(self) -> set:
        return self.get("required_services", set())

    @required_services.setter
    def required_services(self, required_services: set):
        self["required_services"] = required_services

    def set_ports_as_dict(self):
        """replace ports list by a dict with container port as key

        (use str key because later conversion to json)"""
        ports_dict = ports_as_dict(self.ports)
        self.ports = ports_dict

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

    def _check_required(self):
        for key in ("image", "domain"):
            if not self.get(key):
                raise ValueError(f"Site configuration missing '{key}' key")

    def _normalize_ports(self):
        if "ports" not in self:
            self["ports"] = []
            return
        if not isinstance(self.ports, list):
            raise ValueError("Site['ports'] must be a list")
        normalize_ports(self.ports)

    def _normalize_domain(self):
        dom = DomainSplit(self.domain)
        self.domain = dom.full_path()
