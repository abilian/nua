"""Nua postgresql related commands."""
import os
import re
from pathlib import Path

from nua.lib.actions import install_package_list, installed_packages
from nua.lib.console import print_magenta, print_red
from nua.lib.exec import mp_exec_as_postgres
from nua.lib.gen_password import gen_password
from nua.lib.panic import warning
from nua.lib.shell import chown_r, sh

from ..docker_utils import docker_host_gateway_ip

PG_VERSION = "14"
POSTGRES_CONF_PATH = Path(f"/etc/postgresql/{PG_VERSION}/main")
RE_5432 = re.compile(r"\s*port\s*=\s*5432\D")
RE_COMMENT = re.compile(r"\s*#")
RE_LISTEN = re.compile(r"\s*listen_addresses\s*=(.*)$")

# S105 Possible hardcoded password
NUA_PG_PWD_FILE = ".postgres_pwd"  # noqa S105


def postgres_pwd() -> str:
    """Return the 'postgres' user DB password.

      - When used in container context, the env variable NUA_POSTGRES_PASSWORD should
        contain the password.
      - When used in nua-orchestrator context, read the password from local file.

    For orchestrator context, assuming this function can only be used *after* password
    was generated (or its another bug).

    Rem.: No cache. Rarely used function and password can be changed.
    """
    password = os.environ.get("NUA_POSTGRES_PASSWORD")
    if password:
        return password
    file_path = Path("~nua").expanduser() / NUA_PG_PWD_FILE
    with open(file_path, encoding="utf8") as rfile:
        password = rfile.read().strip()
    return password


def set_random_postgres_pwd() -> bool:
    print_magenta("Setting Postgres password")
    return set_postgres_pwd(gen_password(24))


def _store_pg_password(password: str):
    """Store the password in "~nua/.postgres_pwd".

    Expect to be run either by root or nua.
    """
    file_path = Path("~nua").expanduser() / NUA_PG_PWD_FILE
    with open(file_path, "w", encoding="utf8") as wfile:
        wfile.write(f"{password}\n")
    chown_r(file_path, "nua")
    os.chmod(file_path, 0o600)  # noqa: S103


def set_postgres_pwd(password: str) -> bool:
    """Set postgres password for local instance of postgres.

    The password is stored in clear in Nua home. In future version, it
    could be replaced by SSL key, thus gaining the ability to have
    encryption of streams and expiration date. Basically we need clear
    password somewhere. Since this password is only used by Nua scripts
    (if Nua is the only user of local postgres DB), it could also be
    generated / erased at each invocation. Password could be stored in
    some file in the postgres user home (a postgres feature). No test of
    min password length in this function.
    """
    r_pwd = repr(password)
    query = f"ALTER USER postgres PASSWORD {r_pwd}"
    cmd = f'/usr/bin/psql -c "{query}"'
    mp_exec_as_postgres(cmd, cwd="/tmp", show_cmd=False)  # noqa S108
    _store_pg_password(password)
    return True


# XXX: not used
def pg_run_environment(_unused_site: dict) -> dict:
    """Return a dict of environ variable for docker.run().

    Actually, returns the DB postges password. This function to be used
    in orchestrator environment, thus the password will be read from
    host file.
    """
    return {"NUA_POSTGRES_PASSWORD": postgres_pwd()}


def bootstrap_install_postgres() -> bool:
    """Installing the requied Postgres version locally.

    Need to be executed as root at nua install stage
    """
    print_magenta(f"Installation of postgres version {PG_VERSION}")
    # detect prior installation of other versions:
    if not _pg_verify_no_prior_installation():
        return False
    install_package_list(
        [f"postgresql-{PG_VERSION}", "libpq-dev"],
        clean=False,
        keep_lists=True,
    )
    allow_docker_connection()
    return pg_check_installed()


def _pg_verify_no_prior_installation() -> bool:
    conf_path = Path("/etc/postgresql")
    if not conf_path.is_dir():
        return True
    existing = [x.name for x in conf_path.iterdir()]
    bad_version = [x for x in existing if x != PG_VERSION]
    if not bad_version:
        return True
    print_red(
        "Some Postgres installation was found and need to be removed by commands like:"
    )
    for version in bad_version:
        print_red(f"    apt purge -y postgresql-{version}")
    print_red("    apt autoremove -y")
    return False


def pg_check_installed() -> bool:
    """Check that postgres is installed locally."""
    test = _pg_check_installed_version()
    if test:
        test = _pg_check_std_port()
    return test
    # ensure db started
    # sudo systemctl start postgresql


def _pg_check_installed_version() -> bool:
    package = f"postgresql-{PG_VERSION}"
    if package in installed_packages():
        return True
    warning(f"Required package not installed: {package}")
    return False


def _pg_check_std_port() -> bool:
    path = POSTGRES_CONF_PATH / "postgresql.conf"
    if not path.is_file():
        print_red(f"Postgres config file not found: {path}")
        return False
    with open(path, encoding="utf8") as rfile:
        for line in rfile:
            if RE_5432.match(line):
                return True
    print_red("Postgres is expected on standard port 5432, check configuration.")
    return False


def pg_check_listening(_unused_site: dict | None = None) -> bool:
    """Check at deploy time that the postgres daemon is listening on the
    gateway port of the docker service (ip passed as parameter).

    This is launched for every deployed image (so cached).
    """
    if not pg_check_installed():
        return False
    path = POSTGRES_CONF_PATH / "postgresql.conf"
    if not path.is_file():
        print_red(f"Postgres config file not found: {path}")
        return False
    return _actual_check_listening(docker_host_gateway_ip(), path)


def _actual_check_listening(gateway: str, path: Path) -> bool:
    with open(path, encoding="utf8") as rfile:
        for line in rfile:
            if RE_COMMENT.match(line):
                continue
            if (listen_match := RE_LISTEN.match(line)) is not None:
                listening = listen_match[1].strip()
                return _add_gateway_address(listening, gateway)
    return _add_gateway_address("", gateway)


def allow_docker_connection():
    """Check at deploy time that the pg_hba.conf file permit connexion.

    Must be run as root at bootstrap time.
    """
    auth_line = (
        "host    all             all             172.16.0.0/12           password"
    )

    path = POSTGRES_CONF_PATH / "pg_hba.conf"
    if not path.is_file():
        print_red(f"Postgres config file not found: {path}")
        return False
    with open(path, encoding="utf8") as rfile:
        content = rfile.read()
    if auth_line in content:
        return
    with open(path, "a", encoding="utf8") as afile:
        afile.write(auth_line)
        afile.write("\n")


def _save_config_gateway_address(content: str):
    src_path = Path("~/nua_listening_docker.conf.tmp").expanduser()
    with open(src_path, "w", encoding="utf8") as wfile:
        wfile.write(content)
    dest_path = POSTGRES_CONF_PATH / "conf.d" / "nua_listening_docker.conf"

    cmd = f"sudo mv -f {src_path} {dest_path}"
    sh(cmd, show_cmd=False)

    cmd = f"sudo chown postgres:postgres {dest_path}"
    sh(cmd, show_cmd=False)

    cmd = f"sudo chmod 644 {dest_path}"
    sh(cmd, show_cmd=False)


def _add_gateway_address(listening: str, gateway: str) -> bool:
    if not listening:
        content = f"listen_addresses = 'localhost, {gateway}'\n"
        _save_config_gateway_address(content)
        return True
    if gateway in listening or "*" in listening:
        return True

    if listening.endswith("'"):
        value = f"{listening[:-1]}, {gateway}'"
    elif listening.endswith('"'):
        value = f'{listening[:-1]}, {gateway}"'
    else:  # dubious
        value = f"'{listening}, {gateway}'"

    content = f"listen_addresses = {value}'\n"
    _save_config_gateway_address(content)
    return True


def pg_restart_service():
    """Restart postgres service."""
    # cmd = "sudo service postgresql restart"
    cmd = "sudo systemctl restart postgresql"
    sh(cmd)
