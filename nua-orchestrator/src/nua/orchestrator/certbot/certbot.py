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
from importlib import resources as rso
from pathlib import Path
from textwrap import dedent

from nua.lib.console import print_magenta, print_red
from nua.lib.panic import abort, vprint
from nua.lib.tool.state import verbosity

from nua.orchestrator import config

from ..nua_env import certbot_exe, nua_home_path, venv_bin
from .certbot_strategies import (
    apply_auto_strategy,
    apply_none_strategy,
    certbot_invocation,
)

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
        abort(f"Unknown certbot_strategy: {strategy}")


def install_certbot() -> None:
    print_magenta("Installation of Nua certbot configuration")
    _make_folders()
    _copy_configuration()
    _set_cron()


def _make_folders() -> None:
    for path in (
        nua_home_path() / "letsencrypt",
        nua_home_path() / "lib" / "letsencrypt",
        nua_home_path() / "log" / "letsencrypt",
    ):
        path.mkdir(parents=True, exist_ok=True)
        path.chmod(0o755)  # noqa: S103


def _copy_configuration() -> None:
    conf_file = nua_home_path() / "letsencrypt" / "cli.ini"
    conf_file.write_text(
        rso.files(CERTBOT_CONF).joinpath("cli.ini").read_text(encoding="utf8")
    )
    conf_file.chmod(0o644)


def _set_cron() -> None:
    cron_file = Path("/etc/cron.d/nua_certbot")
    cron_file.write_text(_certbot_cron())
    cron_file.chmod(0o644)


def _certbot_cron() -> str:
    if not Path(certbot_exe()).exists():
        raise ValueError(f"Certbot executable not found at '{certbot_exe()}'")
    certbot = certbot_invocation()
    return dedent(
        f"""\
    SHELL=/bin/sh
    PATH={venv_bin()}:/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin

    0 */12 * * * root perl -e 'sleep int(rand(43200))' && {certbot} -q renew
    """
    )
