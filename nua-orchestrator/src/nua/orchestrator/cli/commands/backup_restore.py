"""Execute backup commands."""

from nua.orchestrator.app_management import AppManagement

from .start_stop import start_nua_instance, stop_nua_instance


def backup_all():
    """Execute a one-time backup for all instances having a backup declaration."""
    print("Execute a one-time backup for all instances having a backup declaration.")
    manager = AppManagement()
    result = manager.backup_apps()
    print(result)


def restore_last(*, label: str = "", domain: str = ""):
    """Restore last backup for the app instance identified by its label."""
    print(f"Restore last backup for the app '{label or domain}'")
    stop_nua_instance(label=label, domain=domain)
    manager = AppManagement()
    if label:
        result = manager.restore_app_label(label)
    else:
        result = manager.restore_app_domain(domain)
    print(result)
    start_nua_instance(label=label, domain=domain)
