"""Certbot strategies.

host.certbot_strategy (or ENV NUA_CERTBOT_STRATEGY) can be (for now):
    - auto: all domains are declared to certbot to use HTTPS
    - none: no HTTPS domain, all is converted to HTTP only (i.e. tests or local server)
    - Default is "auto"

Test ENV variables:
    - NUA_CERTBOT_VERBOSE: show certbot log
    - NUA_CERTBOT_TEST: use certbot test environment (pnly for tests)
"""

import os

from nua.lib.panic import show, vprint, vprint_magenta
from nua.lib.shell import sh
from nua.lib.tool.state import verbosity

from nua.orchestrator import config


def certbot_run_args(domains: list) -> str:
    """Build cerbot's arguments for a domain and subdomains.

    (Local function)
    """
    run_args = [
        "--nginx",
        "--keep",
        "--renew-with-new-domains",
        "--allow-subset-of-names",
        "--expand",
        "--agree-tos",
        "-n",
        "--rsa-key-size 4096",
        # "--key-type rsa", for newer certbot versions
        "--redirect",
    ]
    if not os.environ.get("NUA_CERTBOT_VERBOSE"):
        run_args.append("--quiet")
    if os.environ.get("NUA_CERTBOT_TEST"):
        run_args.append("--test-cert")
    admin_mail = config.read("nua", "host", "host_admin_mail")
    if admin_mail:
        email = f"--email {admin_mail}"
    else:
        email = "--register-unsafely-without-email"
    run_args.append(email)
    dom_list = " ".join(f"-d {d}" for d in domains)
    run_args.append(dom_list)
    return " ".join(run_args)


def apply_none_strategy(domains: list[str]):
    with verbosity(1):
        vprint_magenta(f"Use HTTP protocol for: {' '.join(domains)}")
    return


def apply_auto_strategy(domains: list[str]):
    """Convert just created HTTP configuration (by nginx template) to HTTPS
    using certbot (if strategy is 'auto').

    Each domain of the list uses the same SSL key.

    - implementation mode "auto":
        - let certbot rewrite redirections,
        - let certbot manage cron,
        - apply "auto" rules and parameters.
    """
    with verbosity(1):
        vprint_magenta(f"Use HTTPS protocol (Certbot) for: {' '.join(domains)}")
    cmd = "certbot run " + certbot_run_args(domains)
    if os.getuid():  # aka not root
        cmd = "sudo " + cmd
    # Important:
    # - command is executed as root
    # - when "sudo cmd", from nua, we epect to use the host's certbot package
    #   of the host installation (not a venv package)
    # - certbot has been installed on the host from nua-bootstrap
    with verbosity(2):
        show(cmd)
    output = sh(cmd, show_cmd=False, capture_output=True)
    with verbosity(3):
        vprint(output)
