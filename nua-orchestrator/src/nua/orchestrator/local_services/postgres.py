"""Nua postgres as a service."""
from ..db_utils.postgres_utils import (
    pg_check_listening,
    pg_restart_service,
    postgres_pwd,
)
from .local_service_base import LocalServiceBase


class Postgres(LocalServiceBase):
    def aliases(self) -> list:
        return ["postgresql"]

    def check_site_configuration(self, _site: dict | None = None) -> bool:
        return pg_check_listening()

    def restart(self) -> bool:
        pg_restart_service()
        return True

    def environment(self, _site: dict | None = None) -> dict:
        return {"NUA_POSTGRES_PASSWORD": postgres_pwd()}
