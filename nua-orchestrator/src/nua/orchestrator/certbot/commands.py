"""Certbot strategies.

host.certbot_strategy (or ENV NUA_CERTBOT_STRATEGY) can be (for now):

    - auto: all domains are declared to certbot to use HTTPS
    - none: no HTTPS domain, all is converted to HTTP only (i.e. tests or local server)
    - Default is "auto"

Test ENV variables:

    - NUA_CERTBOT_VERBOSE: show certbot log
    - NUA_CERTBOT_TEST: use certbot test environment (only for tests)
"""

import os

from nua.lib.panic import Abort, debug, important, red_line, show
from nua.lib.shell import sh
from nua.lib.tool.state import verbosity

from nua.orchestrator import config

from ..nginx.commands import nginx_is_active, nginx_restart, nginx_stop
from .installer import (
    certbot_invocation_list,
    ensure_letsencrypt_installed,
    letsencrypt_path,
)


def certbot_certonly_command(domain: str, option: str) -> str:
    """Build cerbot's arguments for a subdomains.

    Standalone or nginx call.
    """
    run_args = certbot_invocation_list() + [
        "certonly",
        option,
        "--keep",
        "--no-redirect",
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
    run_args.append(f"-d {domain}")
    return " ".join(run_args)


def apply_none_strategy(_top_domain: str, domains: list[str]) -> None:
    with verbosity(0):
        important(f"Use HTTP protocol for: {' '.join(domains)}")
    return


def cert_exists(domain: str) -> bool:
    """Test if a domain exists in letsencrypt/live/."""
    path = letsencrypt_path() / "live" / domain
    if os.getuid():  # aka not root
        cmd = f"sudo test -d {path} && echo ok || echo ko"
        output = sh(cmd, show_cmd=False, capture_output=True)
        with verbosity(3):
            debug(f"cert_exists() {domain}")
            debug(output)
        return output.strip() == "ok"
    else:
        return path.is_dir()


def gen_cert_standalone(domain: str) -> bool:
    if os.getuid():  # aka not root
        prefix = "sudo "
    else:
        prefix = ""
    standalone_cmd = certbot_certonly_command(domain, "--standalone")
    cmd = f"{prefix}{standalone_cmd}"
    with verbosity(2):
        show(cmd)
    output = ""
    try:
        output = sh(cmd, show_cmd=False, capture_output=True)
    except Abort:
        return False
    if output:
        with verbosity(2):
            debug(output)
    return True


def gen_cert_nginx(domain: str) -> None:
    with verbosity(3):
        debug("known domain, will register with --nginx certbot option:", domain)
    if os.getuid():  # aka not root
        prefix = "sudo "
    else:
        prefix = ""
    nginx_cmd = certbot_certonly_command(domain, "--nginx")
    cmd = f"{prefix}{nginx_cmd}"
    with verbosity(2):
        show(cmd)
    try:
        output = sh(cmd, show_cmd=False, capture_output=True)
    except Abort:
        red_line("Error in shell command.")
        raise
    if output:
        with verbosity(2):
            debug(output)


def apply_auto_strategy(top_domain: str, domains: list[str]) -> bool:
    """Convert just created HTTP configuration (by nginx template) to HTTPS
    using certbot (if strategy is 'auto').

    Each domain of the list uses the same SSL key.

    - implementation mode "auto":
        - let certbot rewrite redirections,
        - let certbot manage cron,
        - apply "auto" rules and parameters.
    """
    ensure_letsencrypt_installed()
    sorted_domains = sorted(domains)
    with verbosity(0):
        important(f"Use HTTPS protocol (Certbot) for: {' '.join(sorted_domains)}")
    # cmd = certbot_run(top_domain, domains)
    # cmd = certbot_certonly(top_domain, domains)
    #
    # If all domain are already known from letsencrypt, we may try a direct
    # reload using nginx (so without killing nginx websites)
    # Else, we need to stop nginx and use the standalone procedure.
    if nginx_is_active(allow_fail=True) and all(
        cert_exists(domain) for domain in sorted_domains
    ):
        for domain in sorted_domains:
            gen_cert_nginx(domain)
    else:
        nginx_stop(allow_fail=True)
        for domain in sorted_domains:
            if not gen_cert_standalone(domain):
                return False
        nginx_restart(allow_fail=False)
    return True
