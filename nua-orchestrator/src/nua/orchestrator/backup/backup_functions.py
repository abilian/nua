"""Functions to backup databases."""
from pathlib import Path

from nua.lib.dates import backup_date

from ..docker_utils import docker_container_of_name, docker_exec_checked
from ..resource import Resource
from ..volume import Volume
from .backup_record import BackupItem
from .backup_report import BackupReport
from .restore_engine import restore_fct_id


def bck_pg_dumpall(resource: Resource, volume: Volume | None = None) -> BackupReport:
    """Backup the Resource with pg_dumpall.

    Resource is expected to be a Postgres database.

    Returns:
        BackupReport instance
    """
    backup_conf = resource.get("backup")
    backup_destination = backup_conf.get("destination", "local")

    if backup_destination != "local":
        return BackupReport(
            node=resource.container_name,
            task=True,
            success=False,
            message="WIP: Only local backup is currently implemented",
            backup_item=None,
        )

    restore_id = restore_fct_id("pg_dumpall")

    # _backup_dir = store.installed_nua_settings()["backup"]["location"]
    file_name = f"{backup_date()}-{resource.container_name}.sql"
    folder = Path("/home/nua/backups") / resource.container_name
    folder.mkdir(exist_ok=True, parents=True)
    dest_file = folder / file_name
    container = docker_container_of_name(resource.container_name)[0]
    cmd = "/usr/bin/pg_dumpall -U ${POSTGRES_USER}"

    print(f"Start backup: {dest_file}")
    try:
        with dest_file.open("wb") as output:
            docker_exec_checked(
                container,
                {"cmd": cmd, "user": "root", "workdir": "/"},
                output,
            )
            output.flush()
    except RuntimeError as e:
        result = BackupReport(
            node=resource.container_name,
            task=True,
            success=False,
            message=f"Backup failed: {e}",
            backup_item=None,
        )
    else:
        backup_item = BackupItem(path=str(dest_file), restore=restore_id)
        result = BackupReport(
            node=resource.container_name,
            task=True,
            success=True,
            message=dest_file.name,
            backup_item=backup_item,
        )
    finally:
        print(result)
        return result
