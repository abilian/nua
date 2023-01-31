"""Function to auto configure a SQLite DB, on a local Docker volume.
"""
from ..resource import Resource
from ..volume import Volume

NUA_PROPERTIES = {
    "name": "sqlite",  # plugin name
    "container": "local",  # container type
    "family": "db",  # plugin family
    "assign": True,  # use the "assign" keyword"
    "network": True,  # here we require docker bridge network only for volume name
}


def configure_db(resource: Resource):
    # create volume:
    sqlite_volume = _make_volume(resource)
    resource.volume_declaration = [sqlite_volume]
    # assign keys in (env) for create or retrieve persistent values
    resource.env = {
        "SQLITE_DIR": sqlite_volume["target"],
        "SQLITE_SOURCE": sqlite_volume["source"],
    }
    resource.assign = [
        {"key": "SQLITE_DB", "unique_db": True, "persist": True},
    ]
    resource.assign_priority = 0


def _make_volume(resource: Resource) -> dict:
    volume = Volume()
    volume.type = "volume"
    volume.driver = "local"
    # at this stage, network_name is defined
    volume.source = f"{resource.resource_name}_{resource.network_name}"
    # target of SQLite
    volume.target = "/nua/app/sqlite"
    return volume.as_dict()


# def setup_db(resource: Resource):
#     """Find or create the required DB for an application user."""
#     # nothing to do here: the sqlite driver will create the file.
