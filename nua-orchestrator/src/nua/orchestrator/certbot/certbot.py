"""Certbot main entry, detect strategy and apply.

host.certbot_strategy (or ENV NUA_CERTBOT_STRATEGY) can be (for now):
    - auto: all domains are declared to certbot to use HTTPS
    - none: no HTTPS domain, all is converted to HTTP only (i.e. tests or local server)
    - Default is "auto"

Test ENV variables:
    - NUA_CERTBOT_VERBOSE: show certbot log
    - NUA_CERTBOT_TEST: use certbot test environment (only for tests)
"""

import os
from pprint import pformat

from nua.lib.console import print_red
from nua.lib.panic import Abort, vprint
from nua.lib.tool.state import verbosity

from nua.orchestrator import config

from .commands import apply_auto_strategy, apply_none_strategy

CERTBOT_CONF = "nua.orchestrator.certbot.config"

ALLOWED_STRATEGY = {"auto": apply_auto_strategy, "none": apply_none_strategy}
STRATEGY_PROTO = {"auto": "https://", "none": "http://"}


def use_https() -> bool:
    return get_certbot_strategy() == "auto"


def register_certbot_domains(apps: list):
    """Apply certbot strategy to domains.

    Group common domains and execute "certbot run".
    (Only public function).
    Warning:
       - Top domain "exemple.com" is NOT configurd for cerbot if only
         "www.exemple.com" is listed,
       - all sub-domains "xxx.exemple.com" share the same key.
    """
    tops = {}
    for site in apps:
        # hostname is "www.exemple.com"
        # -> top domain is "exemple.com"
        domains = tops.get(site.top_domain, set())
        domains.add(site.hostname)
        tops[site.top_domain] = domains
    with verbosity(3):
        print("certbot registration for:")
        print(pformat(tops))
    strategy = get_certbot_strategy()
    strategy_function = ALLOWED_STRATEGY[strategy]
    for top_domain, domains in tops.items():
        strategy_function(top_domain, list(domains))
    with verbosity(3):
        vprint("register_certbot_domains() done")


def get_certbot_strategy() -> str:
    default = "auto"
    strategy = config.read("nua", "host", "certbot_strategy") or default
    strategy = os.environ.get("NUA_CERTBOT_STRATEGY") or strategy
    strategy = strategy.strip().lower()
    assert_valid_certbot_strategy(strategy)
    return strategy


def protocol_prefix() -> str:
    return STRATEGY_PROTO[get_certbot_strategy()]


def assert_valid_certbot_strategy(strategy: str):
    if strategy not in ALLOWED_STRATEGY:
        print_red("Allowed values for certbot_strategy are:")
        print_red(f"{ALLOWED_STRATEGY}")
        raise Abort(f"Unknown certbot_strategy: {strategy}")
