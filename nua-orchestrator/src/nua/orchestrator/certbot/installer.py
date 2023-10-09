"""Certbot package installer.

Install Certbot config files for the nua user at bootstrap time.

TODO: add a cron to revoke domains not instancied sinc a few days.
"""

import os
from importlib import resources as rso
from pathlib import Path
from textwrap import dedent

from nua.lib.console import print_magenta
from nua.lib.shell import sh

from ..nua_env import nua_env

# from .commands import certbot_invocation

CERTBOT_CONF = "nua.orchestrator.certbot.config"


def letsencrypt_path() -> Path:
    return nua_env.nua_home_path() / "letsencrypt"


def certbot_invocation() -> str:
    return " ".join(certbot_invocation_list())


def certbot_invocation_list() -> list[str]:
    return [
        nua_env.certbot_exe(),
        "-c",
        str(letsencrypt_path() / "cli.ini"),
    ]


def copy_rso_file(module: str, name: str, dest_folder: str | Path) -> None:
    dest_file = Path(dest_folder) / name
    dest_file.write_text(rso.files(module).joinpath(name).read_text(encoding="utf8"))
    dest_file.chmod(0o644)


def _installation_found() -> bool:
    for path in (
        nua_env.nua_home_path() / "letsencrypt",
        nua_env.nua_home_path() / "lib" / "letsencrypt",
        nua_env.nua_home_path() / "log" / "letsencrypt",
    ):
        if not path.is_dir():
            return False
    for file in (
        nua_env.nua_home_path() / "letsencrypt" / "cli.ini",
        nua_env.nua_home_path() / "letsencrypt" / "options-ssl-nginx.conf",
    ):
        if not file.is_file():
            return False
    return True


def ensure_letsencrypt_installed() -> None:
    if _installation_found():
        return

    install_certbot()


def install_certbot() -> None:
    print_magenta("Installation of Nua Certbot configuration")
    _make_folders()
    _copy_configuration()
    _generate_dhparam()
    if os.geteuid() == 0:
        _set_cron()


def _make_folders() -> None:
    for path in (
        nua_env.nua_home_path() / "letsencrypt",
        nua_env.nua_home_path() / "lib" / "letsencrypt",
        nua_env.nua_home_path() / "log" / "letsencrypt",
    ):
        path.mkdir(parents=True, exist_ok=True)
        path.chmod(0o755)  # noqa: S103


def _copy_configuration() -> None:
    dest_folder = nua_env.nua_home_path() / "letsencrypt"
    copy_rso_file(CERTBOT_CONF, "cli.ini", dest_folder)
    copy_rso_file(CERTBOT_CONF, "options-ssl-nginx.conf", dest_folder)


def _generate_dhparam() -> None:
    pem_file = nua_env.nua_home_path() / "letsencrypt" / "ssl-dhparams.pem"
    if pem_file.is_file() and pem_file.stat().st_size > 0:
        print_magenta(
            "Existing file 'ssl-dhparams.pem' will be used, no dhparam generation."
        )
        return

    print_magenta("Generating Certbot dhparam")
    cmd = f"openssl dhparam -dsaparam -out {pem_file} 4096"
    if os.getuid():  # aka not root
        cmd = f"sudo {cmd}"
    output = sh(cmd, timeout=3600, show_cmd=True, capture_output=True)
    print(output)


def _set_cron() -> None:
    cron_file = Path("/etc/cron.d/nua_certbot")
    cron_file.write_text(_certbot_cron())
    cron_file.chmod(0o644)


def _certbot_cron() -> str:
    if not Path(nua_env.certbot_exe()).exists():
        raise ValueError(f"Certbot executable not found at '{nua_env.certbot_exe()}'")

    certbot = certbot_invocation()
    return dedent(
        f"""\
        SHELL=/bin/sh
        PATH={nua_env.venv_bin()}:/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin

        0 */12 * * * root perl -e 'sleep int(rand(43200))' && {certbot} -q renew
        """
    )
