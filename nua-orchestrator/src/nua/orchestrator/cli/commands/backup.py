"""Execute backup commands."""

from nua.orchestrator.sites_management import SitesManagement


def backup_all():
    """Execute a one-time backup for all site instance having a backup
    declaration."""
    deployer = SitesManagement()
    result = deployer.backup_sites()
    print(result)


def deployed_config() -> dict:
    """Debug: return the curreent active config."""
    deployer = SitesManagement()
    deployer.load_active_config()
    return deployer.active_config
