"""Nua mariadb as a service."""
from ..mariadb_utils import mariadb_pwd, mariadb_restart_service
from ..service_loader import ServiceBase


class Mariadb(ServiceBase):
    def __init__(self, options: dict):
        super().__init__(options)

    def restart(self) -> bool:
        mariadb_restart_service()
        return True

    def environment(self, _site: dict) -> dict:
        return {"NUA_MARIADB_PASSWORD": mariadb_pwd()}
