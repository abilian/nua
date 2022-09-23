"""Certbot main entry, detect strategy and apply.

host.certbot_strategy (or ENV NUA_CERTBOT_STRATEGY) can be (for now):
    - auto: all domains are declared to certbot to use HTTPS
    - none: no HTTPS domain, all is converted to HTTP only (ie. tests or local server)
    - Default is "auto"

Test ENV variables:
    - NUA_CERTBOT_VERBOSE: show certbot log
    - NUA_CERTBOT_TEST: use certbot test environment (pnly for tests)
"""

import os

from . import config
from .certbot_strategies import apply_auto_strategy, apply_none_strategy
from .rich_console import panic, print_red

ALLOWED_STRATEGY = {"auto": apply_auto_strategy, "none": apply_none_strategy}


def register_certbot_domains(filtered_sites: list):
    """Apply certbot strategy to domains.

    Group common domains and execute "certbot run".
    (Only public function).
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
    strategy = fetch_certbot_strategy()
    apply_function = ALLOWED_STRATEGY[strategy]
    for domains in domain_dict.values():
        apply_function(list(domains))


def fetch_certbot_strategy() -> str:
    default = "auto"
    strategy = config.read("nua", "host", "certbot_strategy") or default
    strategy = os.environ.get("NUA_CERTBOT_STRATEGY") or strategy
    strategy = strategy.strip().lower()
    assert_valid_certbot_strategy(strategy)
    return strategy


def assert_valid_certbot_strategy(strategy: str):
    if strategy not in ALLOWED_STRATEGY:
        print_red("Allowed values for certbot_strategy are:")
        print_red(f"{ALLOWED_STRATEGY}")
        panic(f"Unknown certbot_strategy: {strategy}")
