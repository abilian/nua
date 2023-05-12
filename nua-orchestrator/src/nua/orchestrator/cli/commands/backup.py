"""Execute backup commands."""

from nua.orchestrator.app_management import AppManagement


def backup_all():
    """Execute a one-time backup for all instances having a backup declaration."""
    print("Execute a one-time backup for all instances having a backup declaration.")
    manager = AppManagement()
    result = manager.backup_apps()
    print(result)
