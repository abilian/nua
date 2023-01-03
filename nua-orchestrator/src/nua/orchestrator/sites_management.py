"""class to manage the currently active sites.

General use:
    - load active configuration
    - loop over sites to perform an action (example: backup)
"""

from nua.lib.panic import warning

from .db import store
from .domain_split import DomainSplit
from .site import Site


class SitesManagement:
    """Management of a list of site."""

    def __init__(self):
        self.active_config = {}
        self.sites = []
        self.sites_per_domain = []
        # self.required_services = set()
        # self.available_services = {}

    def load_active_config(self) -> dict:
        "Return the current deployed configuration."
        self.active_config = store.deploy_config_active()
        if not self.active_config:
            warning("The current deployed config is empty.")
            self.sites = []
            return
        self.sites = [
            Site.from_dict(site_conf)
            for site_conf in self.active_config["deployed"]["sites"]
        ]

    def set_sites_per_domain(self):
        domains = {}
        for site in self.sites:
            dom_list = domains.setdefault(DomainSplit(site.domain), [])
            dom_list.append(site)
        self.sites_per_domain = [
            {"hostname": hostname, "sites": sites_list}
            for hostname, sites_list in domains.items()
        ]

    def backup_sites(self) -> str:
        """Execute a one-time backup for all site instance having a backup
        declaration."""
        self.load_active_config()
        result = []
        for site in self.sites:
            result.append(site.do_full_backup())
        return "\n".join(result)
