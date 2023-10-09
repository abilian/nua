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
from typing import Any

from nua.lib.panic import Abort, bold_debug, debug, red_line
from nua.lib.tool.state import verbosity

from nua.orchestrator import config

from ..app_instance import AppInstance
from ..domain_split import DomainSplit
from .commands import apply_auto_strategy, apply_none_strategy

CERTBOT_CONF = "nua.orchestrator.certbot.config"

ALLOWED_STRATEGY = {"auto": apply_auto_strategy, "none": apply_none_strategy}
STRATEGY_PROTO = {"auto": "https://", "none": "http://"}


def use_https() -> bool:
    return get_certbot_strategy() == "auto"


def register_certbot_domains_per_domain(apps_per_domain: list[dict[str, Any]]):
    """Apply certbot strategy to domains, filtering out internal deployments.

    input format:
    [{'hostname': 'test.example.com',
     'apps': [{'domain': 'test.example.com/instance1',
                 'image': 'flask-one:1.2-1',
                 },
                {'domain': 'test.example.com/instance2',
                 'image': 'flask-one:1.2-1',
                 },
                 ...
    """
    fqdns = []
    for host in apps_per_domain:
        if host.get("internal", False):
            # do not require any SSL certificate for internal apps
            continue
        fqdns.append(host["hostname"])
    _register_certbot_domains(fqdns)


def register_certbot_domains(apps: list[AppInstance]) -> None:
    """Apply certbot strategy to domains.

    Group common domains and execute "certbot run".
    (Only public function).
    Warning:
       - Top domain "exemple.com" is NOT configurd for cerbot if only
         "www.exemple.com" is listed,
       - all sub-domains "xxx.exemple.com" share the same key.
    """
    domains = [app.hostname for app in apps]
    _register_certbot_domains(domains)


def _register_certbot_domains(domains_list: list[str]) -> None:
    """Apply certbot strategy to domains.

    Group common domains and execute "certbot run".
    (Only public function).
    Warning:
       - Top domain "exemple.com" is NOT configurd for cerbot if only
         "www.exemple.com" is listed,
       - all sub-domains "xxx.exemple.com" share the same key.
    """
    domains_per_top: dict[str, set] = {}
    for hostname in domains_list:
        dom_split = DomainSplit(hostname)
        top_domain = dom_split.top_domain()
        # hostname is "www.exemple.com"
        # -> top domain is "exemple.com"
        domains = domains_per_top.get(top_domain, set())
        domains.add(hostname)
        domains_per_top[top_domain] = domains
    with verbosity(3):
        bold_debug("certbot registration for:")
        debug(pformat(domains_per_top))
    strategy = get_certbot_strategy()
    strategy_function = ALLOWED_STRATEGY[strategy]
    for top_domain, domains in domains_per_top.items():
        if not strategy_function(top_domain, list(domains)):
            domains_str = ", ".join(list(domains))
            Abort(f"Certbot/Nginx error for {domains_str}")


def get_certbot_strategy() -> str:
    default = "auto"
    strategy = config.read("nua", "host", "certbot_strategy") or default
    strategy = os.environ.get("NUA_CERTBOT_STRATEGY") or strategy
    strategy = strategy.strip().lower()
    check_valid_certbot_strategy(strategy)
    return strategy


def protocol_prefix() -> str:
    return STRATEGY_PROTO[get_certbot_strategy()]


def check_valid_certbot_strategy(strategy: str) -> None:
    if strategy not in ALLOWED_STRATEGY:
        with verbosity(0):
            red_line("Allowed values for certbot_strategy are:")
            red_line(f"{ALLOWED_STRATEGY}")
        raise Abort(f"Unknown certbot strategy: {strategy}")
