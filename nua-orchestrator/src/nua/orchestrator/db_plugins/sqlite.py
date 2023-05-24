"""Function to auto configure a SQLite DB, on a local Docker volume."""
from ..resource import Resource
from ..volume import Volume

NUA_PROPERTIES = {
    "name": "sqlite",  # plugin name
    "container": "local",  # container type
    "family": "db",  # plugin family
    "assign": True,  # receives dynamic assignment of ENV
    "network": True,  # here we require docker bridge network only for volume name
    "meta-packages": [],  # for app-builder infer packages (for future use)
}


def configure_db(resource: Resource):
    # create volume:
    sqlite_volume = _make_volume(resource)
    resource.volume_declaration = [sqlite_volume.as_dict()]
    # assign keys in (env) for create or retrieve persistent values
    resource.env = {
        "SQLITE_DIR": sqlite_volume.target,
        "SQLITE_SOURCE": sqlite_volume.full_name,
        "SQLITE_DB": {"unique_db": True, "persist": True},
    }


def _make_volume(resource: Resource) -> Volume:
    volume = Volume()
    volume.type = "managed"
    volume.driver = "docker"
    # at this stage, network_name is defined
    volume.name = "data"
    volume.label = resource.container_name
    # target of SQLite
    volume.target = "/nua/app/sqlite"
    return volume


# def setup_db(resource: Resource):
#     """Find or create the required DB for an application user."""
#     # nothing to do here: the sqlite driver will create the file.
