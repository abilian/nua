"""Functions to backup databases."""
from pathlib import Path

from nua.lib.dates import backup_date

from ..docker_utils import docker_container_of_name, docker_exec_stdout
from ..resource import Resource
from .backup_report import BackupReport


def bck_pg_dumpall(resource: Resource) -> BackupReport:
    backup_conf = resource.get("backup")
    backup_destination = backup_conf.get("destination", "local")

    if backup_destination != "local":
        return BackupReport(
            node=resource.container_name,
            task=True,
            success=False,
            message="Only local backup is currently implemented",
        )

    # _backup_dir = store.installed_nua_settings()["backup"]["location"]
    file_name = f"{backup_date()}-{resource.container_name}.sql"
    folder = Path("/home/nua/backups") / resource.container_name
    folder.mkdir(exist_ok=True, parents=True)
    dest_file = folder / file_name
    container = docker_container_of_name(resource.container_name)[0]
    cmd = r'sh -c "/usr/bin/pg_dumpall -U \${POSTGRES_USER}"'

    print(f"Start backup: {dest_file}")

    with dest_file.open("wb") as output:
        docker_exec_stdout(
            container,
            {"cmd": cmd, "user": "root", "workdir": "/"},
            output,
        )
        output.flush()

    print(f"End backup: {dest_file}")

    return BackupReport(
        node=resource.container_name,
        task=True,
        success=True,
        message=dest_file,
    )
