from importlib import import_module

from nua.lib.actions import camel_format, snake_format
from nua.lib.console import print_red

from ..db import store

# def test():
#     from .nua_db_setup import setup_nua_db
#
#     setup_nua_db()
#     s = Services()
#     s.load()
#     s.list()


class Services:
    def __init__(self):
        self.configuration_services = {}
        self.loaded = {}

    def load(self):
        self.load_configuration_services()
        self.load_services_modules()

    def list(self):
        print(self.loaded)

    def load_configuration_services(self):
        settings = store.installed_nua_settings()
        listed = settings.get("services", [])
        for conf_service in listed:
            name = conf_service.get("name")
            if not name:
                print_red(
                    "A service in nua configuration is missing mandatory key 'name'."
                )
                continue
            self.configuration_services[name] = conf_service

    def load_services_modules(self):
        base = __name__.split(".")[:-1]
        base.append("services")
        base_name = ".".join(base)
        for service_options in self.configuration_services.values():
            if not service_options.get("enable", True):
                continue
            name = snake_format(service_options["name"])
            module_name = service_options.get("module", name)
            class_name = camel_format(service_options.get("class", name))
            module_path = f"{base_name}.{module_name}"
            try:
                module = import_module(module_path)
                cls = getattr(module, class_name)
            except Exception:
                print_red(
                    f"error loading local service: {name=} {module_name=} {class_name=}"
                )
                continue
            self.loaded[name] = cls(service_options)
