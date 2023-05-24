import typing

from .backup_functions import bck_pg_dumpall
from .backup_report import BackupReport

if typing.TYPE_CHECKING:
    from ..resource import Resource
    from ..volume import Volume


BCK_FUNCTION = {"pg_dumpall": bck_pg_dumpall}


# fixme will use resource as protocol or abstract
def backup_resource(resource: Resource) -> BackupReport:
    """Execute a backup from main 'backup' configuration of a Resource."""
    backup_conf = resource.get("backup")
    if not backup_conf or not isinstance(backup_conf, dict):
        return BackupReport(
            node=resource.container_name,
            message="No backup configuration",
        )
    method = backup_conf.get("method", "")
    function = BCK_FUNCTION.get(method)
    if not function:
        return BackupReport(
            node=resource.container_name,
            task=True,
            success=False,
            message=f"Unknown backup method '{method}'",
        )
    return function(resource)


def backup_volume(resource: Resource, volume: Volume) -> BackupReport:
    """Execute a backup from backup tag of a volume of a Resource."""
    backup_conf = volume.backup
    if not backup_conf or not isinstance(backup_conf, dict):
        return BackupReport(
            node=volume.full_name,
            task=False,
            success=False,
            message="No backup configuration",
        )
    method = backup_conf.get("method", "sync")
    function = BCK_FUNCTION.get(method)
    if not function:
        return BackupReport(
            node=volume.full_name,
            task=True,
            success=False,
            message=f"Unknown backup method '{method}'",
        )
    return function(resource, volume)
