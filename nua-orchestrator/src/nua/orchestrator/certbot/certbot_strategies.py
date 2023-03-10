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

from nua.lib.panic import show, vprint, vprint_magenta
from nua.lib.shell import sh
from nua.lib.tool.state import verbosity

from nua.orchestrator import config

from ..nua_env import certbot_exe, nua_home


def cert_home() -> str:
    return os.path.join(nua_home(), "letsencrypt")


def certbot_invocation_list() -> list[str]:
    return [
        certbot_exe(),
        "--config-dir",
        os.path.join(nua_home(), "letsencrypt"),
        "--work-dir",
        os.path.join(nua_home(), "lib", "letsencrypt"),
        "--logs-dir",
        os.path.join(nua_home(), "log", "letsencrypt"),
    ]


def certbot_invocation() -> str:
    return " ".join(certbot_invocation_list())


def certbot_run(_top_domain: str, domains: list) -> str:
    """Build cerbot's arguments for a domain and subdomains.

    (Local function)
    """
    run_args = certbot_invocation_list() + [
        "run",
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


def certbot_certonly(top_domain: str, domains: list) -> str:
    """Build cerbot's arguments for a domain and subdomains.

    - version with --cert-name
    - no apply auto


    TODO
    - do not use obsolete jammy certbot package (pb // libssl 3.0.2)
      so from 1.20 in Jammy to current certbot 2.4.0
      pip install certbot certbot-nginx
    - => pypi certbot
    - => specific path of cert files for nua
    - => use options with expand, --cert-name --no-redirect
    - => need to analyse ("certbot certificates") for fetch actual cert path
    - => manually update (templates) after certificate generation
    - => see if renewal automation collide with main host certbot cron ?
      Need to generate dedicated cron similar to:

    # /etc/cron.d/certbot: crontab entries for the certbot package
    #
    # Upstream recommends attempting renewal twice a day
    #
    # Eventually, this will be an opportunity to validate certificates
    # haven't been revoked, etc.  Renewal will only occur if expiration
    # is within 30 days.
    #
    # Important Note!  This cronjob will NOT be executed if you are
    # running systemd as your init system.  If you are running systemd,
    # the cronjob.timer function takes precedence over this cronjob.  For
    # more details, see the systemd.timer manpage, or use systemctl show
    # certbot.timer.
    SHELL=/bin/sh
    PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin

    0 */12 * * * root test -x /usr/bin/certbot -a \\!
                   -d /run/systemd/system && perl -e 'sleep int(rand(43200))' &&
                    certbot -q renew


     certbot certonly --nginx --no-redirect --keep --renew-with-new-domains
                 --allow-subset-of-names --expand --agree-tos -n --rsa-key-size 4096
                 --cert-name xxxx.xyz  --email jd@abilian.com -w /home/nua/nginx/www
                 -d test2.xxxx.xyz

     certbot certonly --nginx --keep --renew-with-new-domains --allow-subset-of-names
                 --expand --agree-tos -n --rsa-key-size 4096 --no-redirect
                 --email jd@abilian.com -d test1.xxxx.xyz --cert-name xxxx.xyz

    """
    run_args = certbot_invocation_list + [
        "certonly",
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
    if top_domain:
        run_args.append(f"--cert-name {top_domain}")
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


def apply_none_strategy(_top_domain: str, domains: list[str]):
    with verbosity(1):
        vprint_magenta(f"Use HTTP protocol for: {' '.join(domains)}")
    return


def apply_auto_strategy(top_domain: str, domains: list[str]):
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
    # cmd = certbot_run(top_domain, domains)
    cmd = certbot_certonly(top_domain, domains)
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
