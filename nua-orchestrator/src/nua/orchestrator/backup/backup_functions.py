from .backup_report import BackupReport

# from .resource import Resource


def bck_pg_dumpall(resource: dict) -> BackupReport:
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
    print("Running backup...")
    # Not running backup either ?
    return BackupReport(
        node=resource.container_name, task=True, success=False, message="test"
    )
