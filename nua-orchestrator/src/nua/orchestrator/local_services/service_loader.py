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


class LocalServices:
    def __init__(self):
        self.configuration_services: list[str] = []
        self.loaded: dict[str, type] = {}

    def load(self):
        self.load_configuration_services()
        self.load_services_modules()

    def list(self):
        print(self.loaded)

    def load_configuration_services(self):
        settings = store.installed_nua_settings()
        listed = settings.get("services", [])
        for service_dict in listed:
            name = service_dict.get("name")
            if not name:
                print_red(
                    "A service in nua configuration is missing mandatory key 'name'."
                )
                continue
            if not service_dict.get("enable", True):
                continue
            self.configuration_services.append(name)

    def load_services_modules(self):
        for service_name in self.configuration_services:
            module_name = snake_format(service_name)
            class_name = camel_format(service_name)
            module_path = f"nua.orchestrator.services.{module_name}"
            try:
                module = import_module(module_path)
                cls = getattr(module, class_name)
            except (ModuleNotFoundError, ImportError) as e:
                print_red(
                    f"Error loading local service: {module_name=} {class_name=}\n{e}"
                )
                continue
            self.loaded[service_name] = cls
