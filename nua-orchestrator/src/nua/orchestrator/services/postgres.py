"""Nua postgres as a service."""
from ..db_utils.postgres_utils import (
    pg_check_listening,
    pg_restart_service,
    postgres_pwd,
)
from .service_base import ServiceBase


class Postgres(ServiceBase):
    def __init__(self, options: dict):
        super().__init__(options)

    def aliases(self) -> list:
        return ["postgresql"]

    def check_site_configuration(self, _site: dict | None = None) -> bool:
        return pg_check_listening()

    def restart(self) -> bool:
        pg_restart_service()
        return True

    def environment(self, _site: dict | None = None) -> dict:
        return {"NUA_POSTGRES_PASSWORD": postgres_pwd()}
