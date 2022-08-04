"""Nua main scripts.
"""
# import multiprocessing as mp
import os
import sys

# from contextlib import suppress
from operator import itemgetter
from pathlib import Path
from urllib.parse import urlparse

from . import __version__, config

# from .registry import start_registry_container  # to remove
# from .server_utils.mini_log import log, log_me, log_sentinel
from .server_utils.mini_log import log_me

# import psutil

# from .server_utils.net_utils import check_port_available, verify_ports_availability

# from time import sleep


# NOTE: /tmp is not ideal, but /run would require some privileges: see later.
# see later for log module implementation


def verify_private_host_key_defined():
    host_key = config.read("nua", "host", "host_priv_key_blob")
    if not host_key:
        msg = (
            "No RSA host key found in local configuration "
            "'nua.host.host_priv_key_blob'.\n"
            "Use script 'nua-adm-gen-host-key' to generate the host key.\n"
            "Server startup aborted."
        )
        log_me(msg)
        print(msg)
        sys.exit(1)


def display_configured_registries():
    """Show configured registries."""
    registries = config.read("nua", "registry")
    print("Configured registries:")
    for reg in sorted(registries, key=itemgetter("priority")):
        msg = (
            f'  priority: {reg["priority"]:>2}   '
            f'format: {reg["format"]:<16}   '
            f'url: {reg["url"]}'
        )
        print(msg)


def status(_cmd: str = ""):
    """Send some status information about local installation."""
    # fixme: go further on status details (sub servers...)
    print(f"Nua version: {__version__}")
    os.environ["NUA_LOG_FILE"] = config.read("nua", "server", "log_file")
    display_configured_registries()
