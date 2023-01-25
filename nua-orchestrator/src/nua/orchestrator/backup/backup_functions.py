from .backup_report import BackupReport

# from .resource import Resource


def bck_pg_dumpall(resource: dict) -> BackupReport:
    backup_conf = resource.get("backup")
    if backup_conf.get("destination", "local") != "local":
        return BackupReport(
            node=resource.container_name,
            task=True,
            success=False,
            message="Only local backup is implemented",
        )
    # _backup_dir = store.installed_nua_settings()["backup"]["location"]
    print("doing backup...")
    return BackupReport(
        node=resource.container_name, task=True, success=False, message="test"
    )
