"""Execute backup commands."""
from nua.orchestrator.app_manager import AppManager


def backup_all_apps():
    """Execute a one-time backup for all instances having a backup declaration."""
    print("Execute a one-time backup for all instances having a backup declaration.")
    manager = AppManager()
    result = manager.backup_all_apps()
    print(result)


def backup_one_app(*, label: str = "", domain: str = ""):
    """Execute a one-time backup for the app instance identified by its label."""
    print(f"Execute a one-time backup for the app '{label or domain}'")
    manager = AppManager()
    if label:
        result = manager.backup_app_label(label)
    else:
        result = manager.backup_app_domain(domain)
    print(result)


def restore_last_backup(*, label: str = "", domain: str = ""):
    """Restore last backuped data for the app instance identified by its label or domain."""
    print(f"Restore last backup for the app identified by '{label or domain}'")
    # pause_nua_instance(label=label, domain=domain)
    # print("-" * 60)
    manager = AppManager()
    if label:
        result = manager.restore_backup_app_per_label(label)
    else:
        result = manager.restore_backup_app_per_domain(domain)
    print(result)
    # print("-" * 60)
    # unpause_nua_instance(label=label, domain=domain)


def restore_list_backups(*, label: str = "", domain: str = ""):
    """List available backups for the app instance identified by its label or domain."""
    print(f"available backups for the app identified by '{label or domain}'")
    manager = AppManager()
    if label:
        result = manager.restore_list_backups_app_per_label(label)
    else:
        result = manager.restore_list_backups_app_per_domain(domain)
    print(result)
