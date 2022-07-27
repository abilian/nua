"""Nua main scripts.
"""
# import multiprocessing as mp
import os
import sys
from contextlib import suppress
from pathlib import Path

import psutil

from . import config
from .registry import start_registry_container  # to remove
from .server_utils.mini_log import log, log_me, log_sentinel
from .server_utils.net_utils import check_port_available, verify_ports_availability

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


def status(_cmd: str = "") -> int:
    """Send some status information about local installation."""
    # fixme: go further on status details (sub servers...)
    os.environ["NUA_LOG_FILE"] = config.read("nua", "server", "log_file")
    print("wip")
