"""Nua mariadb as a service."""
from ..db_utils.mariadb_utils import mariadb_pwd, mariadb_restart_service
from .local_service_base import LocalServiceBase


class Mariadb(LocalServiceBase):
    def restart(self) -> bool:
        mariadb_restart_service()
        return True

    def environment(self, _site: dict | None = None) -> dict:
        return {"NUA_MARIADB_PASSWORD": mariadb_pwd()}
