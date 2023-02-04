"""Execute backup commands."""

from nua.orchestrator.app_management import AppManagement


def backup_all():
    """Execute a one-time backup for all site instance having a backup
    declaration."""
    deployer = AppManagement()
    result = deployer.backup_apps()
    print(result)


def deployed_config() -> dict:
    """Debug: return the curreent active config."""
    deployer = AppManagement()
    deployer.load_active_config()
    return deployer.active_config
