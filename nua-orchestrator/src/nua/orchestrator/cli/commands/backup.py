"""Execute backup commands."""

from nua.orchestrator.app_management import AppManagement


def backup_all():
    """Execute a one-time backup for all site instance having a backup
    declaration."""
    deployer = AppManagement()
    result = deployer.backup_apps()
    print(result)
