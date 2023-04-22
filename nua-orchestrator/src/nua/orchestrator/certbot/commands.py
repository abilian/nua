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
from pathlib import Path

from nua.lib.panic import important, show, vprint
from nua.lib.shell import sh
from nua.lib.tool.state import verbosity

from nua.orchestrator import config

from ..nginx.cmd import nginx_is_active, nginx_restart, nginx_stop
from ..nua_env import certbot_exe, nua_home_path


def letsencrypt_path() -> Path:
    return nua_home_path() / "letsencrypt"


def certbot_invocation_list() -> list[str]:
    return [
        certbot_exe(),
        "-c",
        str(letsencrypt_path() / "cli.ini"),
    ]


def certbot_invocation() -> str:
    return " ".join(certbot_invocation_list())


def certbot_certonly(domain: str, option: str) -> str:
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


def apply_none_strategy(_top_domain: str, domains: list[str]):
    with verbosity(1):
        important(f"Use HTTP protocol for: {' '.join(domains)}")
    return


def cert_exists(domain: str) -> bool:
    path = letsencrypt_path() / "live" / domain
    if os.getuid():  # aka not root
        cmd = f"sudo test -d {path} && echo ok || echo ko"
        output = sh(cmd, show_cmd=False, capture_output=True)
        return output.strip() == "ok"
    else:
        return path.is_dir()


def gen_cert_standalone(domain: str):
    if os.getuid():  # aka not root
        prefix = "sudo "
    else:
        prefix = ""
    standalone_cmd = certbot_certonly(domain, "--standalone")
    cmd = f"{prefix}{standalone_cmd}"
    with verbosity(2):
        show(cmd)
    output = sh(cmd, show_cmd=False, capture_output=True)
    with verbosity(2):
        vprint(output)
    # cmd = f"{prefix}systemctl start nginx"
    # with verbosity(2):
    #     show(cmd)
    # output = sh(cmd, show_cmd=False, capture_output=True)
    # with verbosity(3):
    #     vprint(output)


def gen_cert_nginx(domain: str):
    with verbosity(3):
        print("known domain, will register with --nginx certbot option:", domain)
    if os.getuid():  # aka not root
        prefix = "sudo "
    else:
        prefix = ""
    nginx_cmd = certbot_certonly(domain, "--nginx")
    cmd = f"{prefix}{nginx_cmd}"
    with verbosity(2):
        show(cmd)
    output = sh(cmd, show_cmd=False, capture_output=True)
    with verbosity(2):
        vprint(output)
    # replaced by deploy-hook tag in cli.ini :
    # cmd = f"{prefix}systemctl reload-or-restart nginx"
    # with verbosity(2):
    #     show(cmd)
    # output = sh(cmd, show_cmd=False, capture_output=True)
    # with verbosity(3):
    #     vprint(output)


def apply_auto_strategy(top_domain: str, domains: list[str]):
    """Convert just created HTTP configuration (by nginx template) to HTTPS
    using certbot (if strategy is 'auto').

    Each domain of the list uses the same SSL key.

    - implementation mode "auto":
        - let certbot rewrite redirections,
        - let certbot manage cron,
        - apply "auto" rules and parameters.
    """
    sorted_domains = sorted(domains)
    with verbosity(1):
        important(f"Use HTTPS protocol (Certbot) for: {' '.join(sorted_domains)}")
    # cmd = certbot_run(top_domain, domains)
    # cmd = certbot_certonly(top_domain, domains)
    #
    # If all domain are already known from letsencrypt, we may try a direct
    # reload using nginx (so without killing nginx websites)
    # Else, we need to stop nginx and use the standalone procedure.
    if nginx_is_active() and all(cert_exists(domain) for domain in sorted_domains):
        for domain in sorted_domains:
            gen_cert_nginx(domain)
    else:
        nginx_stop()
        for domain in sorted_domains:
            gen_cert_standalone(domain)
        nginx_restart()
