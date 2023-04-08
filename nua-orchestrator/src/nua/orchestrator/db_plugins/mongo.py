"""Function to auto configure a MongoDB container DB."""

from ..resource import Resource
from ..volume import Volume

NUA_PROPERTIES = {
    "name": "mongo",  # plugin name
    "container": "docker",  # container type
    "family": "db",  # plugin family
    "assign": True,  # receives dynamic assignment of ENV
    "network": True,  # require docker bridge network
    "meta-packages": [],  # for app-builder (future use))
}


def configure_db(resource: Resource):
    # resource.image was set earlier at detect requirement stage
    # create volume:
    resource.volume = [_make_volume(resource)]
    # other options
    # docker params:
    resource.docker = {
        "detach": True,
        "restart_policy": {"name": "always"},
    }
    # env
    resource.env = {
        "MONGO_PORT": "27017",
        "MONGO_INITDB_ROOT_USERNAME": {
            "unique_user": True,
            "persist": True,
        },
        "MONGO_INITDB_ROOT_PASSWORD": {
            "random": True,
            "type": "str",
            "length": 24,
            "persist": True,
        },
    }


def _make_volume(resource: Resource) -> dict:
    volume = Volume()
    volume.type = "volume"
    volume.driver = "local"
    # at this stage, network_name is defined
    volume.source = f"{resource.resource_name}_{resource.network_name}"
    # target of MongoDB images default configuration
    volume.target = "/data/db"
    return volume.as_dict()
