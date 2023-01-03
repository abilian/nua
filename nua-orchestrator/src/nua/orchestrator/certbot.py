"""Certbot main entry, detect strategy and apply.

host.certbot_strategy (or ENV NUA_CERTBOT_STRATEGY) can be (for now):
    - auto: all domains are declared to certbot to use HTTPS
    - none: no HTTPS domain, all is converted to HTTP only (ie. tests or local server)
    - Default is "auto"

Test ENV variables:
    - NUA_CERTBOT_VERBOSE: show certbot log
    - NUA_CERTBOT_TEST: use certbot test environment (only for tests)
"""

import os

from nua.lib.console import print_red
from nua.lib.panic import abort
from nua.lib.tool.state import verbosity

from . import config
from .certbot_strategies import apply_auto_strategy, apply_none_strategy

ALLOWED_STRATEGY = {"auto": apply_auto_strategy, "none": apply_none_strategy}
STRATEGY_PROTO = {"auto": "https://", "none": "http://"}


def register_certbot_domains(sites: list):
    """Apply certbot strategy to domains.

    Group common domains and execute "certbot run".
    (Only public function).
    Warning:
       - Top domain "exemple.com" is NOT configurd for cerbot if only
         "www.exemple.com" is listed,
       - all sub-domains "xxx.exemple.com" share the same key.
    """
    tops = {}
    for site in sites:
        hostname = site.hostname
        # hostname is "www.exemple.com"
        # -> top domain is "exemple.com"
        top_domain = ".".join(hostname.split(".")[-2:])
        domains = tops.get(top_domain, set())
        domains.add(hostname)
        tops[top_domain] = domains
    strategy = get_certbot_strategy()
    strategy_function = ALLOWED_STRATEGY[strategy]
    for domains in tops.values():
        strategy_function(list(domains))
    if verbosity(3):
        print("register_certbot_domains() done")


def get_certbot_strategy() -> str:
    default = "auto"
    strategy = config.read("nua", "host", "certbot_strategy") or default
    strategy = os.environ.get("NUA_CERTBOT_STRATEGY") or strategy
    strategy = strategy.strip().lower()
    assert_valid_certbot_strategy(strategy)
    return strategy


def protocol_prefix():
    return STRATEGY_PROTO[get_certbot_strategy()]


def assert_valid_certbot_strategy(strategy: str):
    if strategy not in ALLOWED_STRATEGY:
        print_red("Allowed values for certbot_strategy are:")
        print_red(f"{ALLOWED_STRATEGY}")
        abort(f"Unknown certbot_strategy: {strategy}")
