"""Execute backup commands.
"""
from nua.lib.tool.state import verbosity

from ..sites_management import SitesManagement


def backup_all():
    """Execute a one-time backup for all site instance having a backup declaration."""
    deployer = SitesManagement()
    deployer.backup_sites()


def deployed_config() -> dict:
    """Debug: return the curreent active config."""
    deployer = SitesManagement()
    deployer.load_active_config()
    return deployer.active_config
