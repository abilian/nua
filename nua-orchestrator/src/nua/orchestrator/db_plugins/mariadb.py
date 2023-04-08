"""Function to auto configure a Mariadb container DB."""
# from nua.agent.db.mariadb_manager import MariadbManager

from ..resource import Resource
from ..volume import Volume

NUA_PROPERTIES = {
    "name": "mariadb",  # plugin name
    "container": "docker",  # container type
    "family": "db",  # plugin family
    "assign": True,  # receives dynamic assignment of ENV
    "network": True,  # require docker bridge network
    "meta-packages": ["mariadb-client"],  # for app-builder (for future use)
}


def configure_db(resource: Resource):
    # resource.image was set earlier at detect requirement stage
    # create volume:
    resource.volume = [_make_volume(resource)]
    # other options
    # docker params:
    resource.docker = {"detach": True, "restart_policy": {"name": "always"}}
    # env
    env = {
        "MARIADB_PORT": "3306",
        "MARIADB_ROOT_PASSWORD": {
            "random": True,
            "type": "str",
            "length": 24,
            "persist": True,
        },
    }
    if resource.get("create_user", True):
        env.update(
            {
                "MARIADB_USER": {
                    "unique_user": True,
                    "persist": True,
                },
                "MARIADB_PASSWORD": {
                    "random": True,
                    "type": "str",
                    "length": 24,
                    "persist": True,
                },
            }
        )
    if resource.get("create_db", True):
        env.update(
            {
                "MARIADB_DATABASE": {"unique_db": True, "persist": True},
            }
        )
    resource.env = env


def _make_volume(resource: Resource) -> dict:
    volume = Volume()
    volume.type = "volume"
    volume.driver = "local"
    # at this stage, network_name is defined
    volume.source = f"{resource.resource_name}_{resource.network_name}"
    # target of Mariadb images default configuration
    volume.target = "/var/lib/mysql"
    return volume.as_dict()


# def setup_db(resource: Resource):
#     """Find or create the required DB for an application user."""
#     # nothing to do here: the postgres container should have created a DB at start
#     if resource.create_db == True (which is the default).
