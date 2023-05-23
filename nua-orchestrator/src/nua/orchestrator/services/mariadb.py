"""Nua mariadb as a service."""
from ..db_utils.mariadb_utils import mariadb_pwd, mariadb_restart_service
from .service_base import ServiceBase


class Mariadb(ServiceBase):
    def restart(self) -> bool:
        mariadb_restart_service()
        return True

    def environment(self, _site: dict | None = None) -> dict:
        return {"NUA_MARIADB_PASSWORD": mariadb_pwd()}
