"""Certbot rules."""

import os
import sys

from . import config
from .rich_console import print_magenta, print_red
from .shell import sh
from .state import verbosity


def assert_certbot_strategy():
    certbot_strategy = config.read("nua", "host", "certbot_strategy")
    if certbot_strategy != "auto":
        print_red("Error: only certbot_strategy='auto' is implemented. Exiting.")
        sys.exit(1)


def register_certbot_domains(filtered_sites: list):
    """Group common domains and execute "certbot run".

    Warning:
       - Top domain "exemple.com" is NOT configurd for cerbot if only
         "www.exemple.com" is listed,
       - all sub-domains "xxx.exemple.com" share the same key.
    """
    domain_dict = {}
    for site in filtered_sites:
        site_domain = site["domain"]
        # site_domain is "www.exemple.com"
        # -> top_domain is "exemple.com"
        top_domain = ".".join(site_domain.split(".")[-2:])
        domains = domain_dict.get(top_domain, set())
        domains.add(site_domain)
        domain_dict[top_domain] = domains
    for domains in domain_dict.values():
        certbot_run_https(list(domains))


def certbot_run_args(domains: list) -> str:
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


def certbot_run_https(domains: list[str]):
    """Convert just created http configuration to https using certbot.

    Each domain of the list uses the same ssl key.

    - implementation mode "auto":
        - let certbot rewrite redirections
        - let certbot manage cron
        - apply "auto" rules and parameters
    """
    assert_certbot_strategy()
    if verbosity(1):
        print_magenta(f"Run Certbot for: {' '.join(domains)}")
    cmd = "certbot run " + certbot_run_args(domains)
    if os.getuid():  # aka not root
        cmd = "sudo " + cmd
    # Important:
    # - command is executed as root
    # - when "sudo cmd", from nua, we epect to use the host's certbot package
    #   of the host installation (not a venv package)
    # - certbot has been installed on the host from nua-bootstrap
    if verbosity(3):
        output = sh(cmd, show_cmd=True, capture_output=True)
        print(output)
    else:
        sh(cmd, show_cmd=verbosity(2))
