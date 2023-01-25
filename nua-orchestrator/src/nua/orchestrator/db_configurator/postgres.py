"""Function to auto configure a Postgres container DB.
"""
from nua.runtime.db.postgres_manager import PostgresManager

from ..resource import Resource
from ..volume import Volume


def configure_db(resource: Resource):
    # resource.image was set earlier at detect requirement stage
    # create volume:
    resource.volume = [_make_volume(resource)]
    # other options
    # docker params:
    resource.run = {"detach": True, "restart_policy": {"name": "always"}}
    # env
    resource.run_env = {"POSTGRES_PORT": "5432"}
    # assign keys in (env) for create or retrieve persistent values
    # Note: POSTGRES_DB could be same as POSTGRES_USER, but prefer to assign both
    # to let the using app retrieving the both values if needed.
    resource.assign = [
        {"key": "POSTGRES_PASSWORD", "random_str": True, "persist": True},
        {"key": "POSTGRES_USER", "unique_user": True, "persist": True},
        {"key": "POSTGRES_DB", "unique_db": True, "persist": True},
        {"key": "USER_PASSWORD", "random_str": True, "persist": True},
    ]
    resource.assign_priority = 0


def _make_volume(resource: Resource) -> dict:
    volume = Volume()
    volume.type = "volume"
    volume.driver = "local"
    # at this stage, network_name is defined
    volume.source = f"{resource.resource_name}_{resource.network_name}"
    # target of Postgres images default configuration
    volume.target = "/var/lib/postgresql/data"
    return volume.as_dict()


def setup_db(resource: Resource):
    """Find or create the required DB for an application user."""
    manager = PostgresManager(
        host=resource.container,
        port="5432",
    )
    manager.wait_for_db()
    manager.setup_db_user(
        resource.run_env["POSTGRES_DB"],
        resource.run_env["POSTGRES_USER"],
        resource.run_env["USER_PASSWORD"],
    )
