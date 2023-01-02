from .resource import Resource
from .volume import Volume


def backup_resource(resource: Resource):
    """Execute a backup from mais backup tag of a Resource."""
    if not (_backup_conf := resource.get("backup")):
        assert _backup_conf  # FIXME: remove this line once the function in implemented
        return


def backup_volume(volume: Volume):
    """Execute a backup from mais backup tag of a Resource."""
    if not (_backup_conf := volume.get("backup")):
        assert _backup_conf  # FIXME: remove this line once the function in implemented
        return
