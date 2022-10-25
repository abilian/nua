"""Nua postgres-docker as a service."""
from ..postgres_utils import pg_check_listening, pg_restart_service, postgres_pwd
from ..service_base import ServiceBase


class PostgresDocker(ServiceBase):
    def __init__(self, options: dict):
        super().__init__(options)

    def aliases(self) -> list:
        return ["postgresql-docker", "postgres_docker", "postgresql_docker"]

    def environment(self, _site: dict | None = None) -> dict:
        # return {"NUA_POSTGRES_PASSWORD": postgres_pwd()}
        return {}
