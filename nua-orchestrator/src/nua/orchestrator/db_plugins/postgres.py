"""Function to auto configure a Postgres container DB."""
# from nua.agent.db.postgres_manager import PostgresManager
from ..resource import Resource
from ..volume import Volume

NUA_PROPERTIES = {
    "name": "postgres",  # plugin name
    "container": "docker",  # container type
    "family": "db",  # plugin family
    "assign": True,  # receives dynamic assignment of ENV
    "network": True,  # require docker bridge network
    "backup_cmd": ["]bck_pg_dumpall"],  # list of available backup commands
}


def configure_db(resource: Resource):
    # resource.image was set earlier at detect requirement stage
    # create volume:
    volume = _make_volume(resource)

    # resource.volume_declaration = [volume.as_dict()]
    resource.volumes = [volume.as_dict()]
    # other options
    # docker params:
    resource.docker = {
        "detach": True,
        "restart_policy": {"name": "always"},
    }
    # env
    resource.env = {
        "POSTGRES_PORT": "5432",
        "POSTGRES_PASSWORD": {
            "random": True,
            "type": "str",
            "length": 24,
            "persist": True,
        },
        "POSTGRES_USER": {"unique_user": True, "persist": True},
        "POSTGRES_DB": {"unique_db": True, "persist": True},
    }


def _make_volume(resource: Resource) -> Volume:
    volume = Volume()
    volume.type = "managed"
    volume.driver = "docker"
    # at this stage, network_name is defined
    volume.name = f"{resource.container_name}-data"
    volume.label = volume.name
    # target of Postgres images default configuration
    volume.target = "/var/lib/postgresql/data"
    return volume


# def setup_db(resource: Resource):
#     """Find or create the required DB for an application user."""
#     # nothing to do here: the postgres container should have created a DB at start.
