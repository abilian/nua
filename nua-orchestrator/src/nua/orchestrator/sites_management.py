"""class to manage the currently active sites.

General use:
    - load active configuration
    - loop over sites to perform an action (example: backup)
"""
import time
from collections.abc import Callable
from copy import deepcopy
from pathlib import Path
from pprint import pformat

import tomli
from nua.lib.console import print_green, print_magenta, print_red
from nua.lib.panic import error, info, warning
from nua.lib.tool.state import verbosity

from . import config
from .certbot import protocol_prefix, register_certbot_domains
from .db import store
from .db.model.deployconfig import ACTIVE, INACTIVE, PREVIOUS
from .db.model.instance import RUNNING
from .deploy_utils import (
    create_container_private_network,
    deactivate_all_instances,
    deactivate_site,
    extra_host_gateway,
    load_install_image,
    mount_resource_volumes,
    port_allocator,
    pull_resource_container,
    start_container_engine,
    start_one_container,
    unused_volumes,
)
from .domain_split import DomainSplit
from .healthcheck import HealthCheck
from .nginx_util import (
    chown_r_nua_nginx,
    clean_nua_nginx_default_site,
    configure_nginx_hostname,
    nginx_restart,
)
from .requirement_evaluator import instance_key_evaluator
from .resource import Resource
from .service_loader import Services
from .site import Site
from .volume import Volume


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

    def backup_sites(self):
        """Execute a one-time backup for all site instance having a backup
        declaration."""
        self.load_active_config()
        for site in self.sites:
            site.do_full_backup()
