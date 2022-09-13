"""Nua postgresql related commands."""
import functools
import re
from pathlib import Path

import psycopg2
from psycopg2.sql import SQL, Identifier

from .actions import install_package_list, installed_packages
from .exec import mp_exec_as_postgres
from .rich_console import print_magenta, print_red
from .shell import sh

PG_VERSION = "14"
POSTGRES_CONF_PATH = Path(f"/etc/postgresql/{PG_VERSION}/main")
RE_ANY_PG = re.compile(r"^postgresql-[0-9\.]+/")
RE_5432 = re.compile(r"\s*port\s*=\s*5432\D")
RE_COMMENT = re.compile(r"\s*#")
RE_LISTEN = re.compile(r"\s*listen_addresses\s*=(.*)$")


def postgres_pwd() -> str:
    """See later how to get the postgres password of postgres user."""
    return "the_pass"


def set_postgres_pwd():
    """Set *hardcoded* postgres password for local instance of postgres.

    See later how to get the postgres password of postgres user.
    """
    print_magenta("Setting Postgres password")
    orig_passwd = "the_pass"  # FIXME, of course.
    # i_pwd = Identifier(orig_passwd)
    r_pwd = repr(orig_passwd)
    # query = SQL("ALTER USER postgres PASSWORD {}".format(i_pwd))
    query = f"ALTER USER postgres PASSWORD {r_pwd}"
    cmd = ["psql", "-c", query]
    mp_exec_as_postgres(cmd)
    return True


def bootstrap_install_postgres() -> bool:
    """Installing the requied Postgres version locally.

    Need to be executed as root at nua install stage
    """
    print_magenta(f"Installation of postgres version {PG_VERSION}")
    # detect prior installation of other versions:
    if not _pg_verify_no_prior_installation():
        return False
    install_package_list([f"postgresql-{PG_VERSION}", "libpq-dev"])
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
    pg_package = f"postgresql-{PG_VERSION}/"
    found = [s for s in installed_packages() if s.startswith(pg_package)]
    if not found:
        print_red(f"Required package not installed: postgresql-{PG_VERSION}")
        return False
    return True


def _pg_check_std_port() -> bool:
    path = POSTGRES_CONF_PATH / "postgresql.conf"
    if not path.is_file():
        print_red(f"Postgres config file not found: {path}")
        return False
    with open(path, "r", encoding="utf8") as rfile:
        for line in rfile:
            if RE_5432.match(line):
                return True
    print_red("Postgres is expected on standard port 5432, check configuration.")
    return False


@functools.cache
def pg_check_listening(gateway: str) -> bool:
    """Check at deploy time that the postgres daemon is listening on the gateway port
    of the docker service (ip passed as parameter).

    This is launched for every deployed image (so cached).
    """
    if not pg_check_installed():
        return False
    path = POSTGRES_CONF_PATH / "postgresql.conf"
    if not path.is_file():
        print_red(f"Postgres config file not found: {path}")
        return False
    return _actual_check_listening(gateway, path)


def _actual_check_listening(gateway: str, path: Path) -> bool:
    with open(path, "r", encoding="utf8") as rfile:
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
    with open(path, "r", encoding="utf8") as rfile:
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
    cmd = "sudo service postgresql restart"
    sh(cmd)


def pg_setup_db_user(host: str, dbname: str, user: str, password: str):
    """Create a postgres user if needed."""
    if not pg_user_exist(host, user):
        pg_user_create(host, user, password)
    if not pg_db_exist(host, dbname):
        pg_db_create(host, dbname, user)


def pg_remove_db_user(host: str, dbname: str, user: str):
    """Remove a postgres user if needed."""
    if pg_db_exist(host, dbname):
        pg_db_drop(host, dbname)
    if pg_user_exist(host, user):
        pg_user_drop(host, user)


def pg_db_drop(host: str, dbname: str):
    """Basic drop database.

    See pg_remove_db_user
    """
    connection = psycopg2.connect(
        dbname="postgres", user="postgres", host=host, password=postgres_pwd()
    )
    connection.autocommit = True
    with connection:
        with connection.cursor() as cur:
            query = "REVOKE CONNECT ON DATABASE {db} FROM public"
            cur.execute(SQL(query).format(db=Identifier(dbname)))
        with connection.cursor() as cur:
            query = "DROP DATABASE {db}"
            cur.execute(SQL(query).format(db=Identifier(dbname)))
    connection.close()


def pg_db_dump(dbname: str, options_str: str = ""):
    """Basic pg_dump call.

    FIXME: not ok for remote host
    """
    cmd = f"pg_dump {dbname} {options_str}"
    mp_exec_as_postgres(cmd)


def pg_user_drop(host: str, user: str) -> bool:
    """Drop user (wip, not enough)."""
    connection = psycopg2.connect(host=host, user="postgres", password=postgres_pwd())
    connection.autocommit = True
    with connection:  # noqa SIM117
        with connection.cursor() as cur:
            query = "DROP USER IF EXISTS {username}"
            cur.execute(SQL(query).format(username=Identifier(user)))
    connection.close()


def pg_user_exist(host: str, user: str) -> bool:
    """Test if a postgres user exists."""
    connection = psycopg2.connect(host=host, user="postgres", password=postgres_pwd())
    connection.autocommit = True
    with connection:  # noqa SIM117
        with connection.cursor() as cur:
            query = "SELECT COUNT(*) FROM pg_catalog.pg_roles WHERE rolname = %s"
            cur.execute(SQL(query), (user,))
            (count,) = cur.fetchone()
    connection.close()
    return count != 0


def pg_user_create(host: str, user: str, password: str):
    """Create a postgres user.

    Assuming standard port == 5432
    """
    connection = psycopg2.connect(host=host, user="postgres", password=postgres_pwd())
    with connection:  # noqa SIM117
        with connection.cursor() as cur:
            # or:  CREATE USER user WITH ENCRYPTED PASSWORD 'pwd'
            query = "CREATE ROLE {username} LOGIN PASSWORD %s"
            cur.execute(SQL(query).format(username=Identifier(user)), (password,))
            cur.execute("COMMIT")
    connection.close()


def pg_db_create(host: str, dbname: str, user: str):
    """Create a postgres DB.

    Assuming standard port == 5432
    """
    connection = psycopg2.connect(
        host=host, dbname="postgres", user="postgres", password=postgres_pwd()
    )
    connection.autocommit = True
    cur = connection.cursor()
    query = "CREATE DATABASE {db} OWNER {user}"
    cur.execute(SQL(query).format(db=Identifier(dbname), user=Identifier(user)))
    connection.close()
    connection = psycopg2.connect(
        host=host, dbname="postgres", user="postgres", password=postgres_pwd()
    )
    connection.autocommit = True
    with connection:  # noqa SIM117
        with connection.cursor() as cur:
            # not this: WITH GRANT OPTION;"
            query = "GRANT ALL PRIVILEGES ON DATABASE {db} TO {user}"
            cur.execute(SQL(query).format(db=Identifier(dbname), user=Identifier(user)))
    connection.close()


def pg_db_exist(host: str, dbname: str) -> bool:
    "Test if the named postgres database exists."
    connection = psycopg2.connect(
        host=host, dbname="postgres", user="postgres", password=postgres_pwd()
    )
    connection.autocommit = True
    with connection:  # noqa SIM117
        with connection.cursor() as cur:
            query = "SELECT datname FROM pg_database"
            cur.execute(SQL(query))
            results = cur.fetchall()
    connection.close()
    db_set = {x[0] for x in results if x}
    return dbname in db_set


def pg_db_table_exist(
    host: str, dbname: str, user: str, password: str, table: str
) -> bool:
    """Check if the named database exists (for host, connecting as user), assuming
    DB exists."""
    connection = psycopg2.connect(
        host=host, dbname=dbname, user=user, password=password
    )
    with connection:
        with connection.cursor() as cur:
            query = "SELECT COUNT(*) FROM information_schema.tables WHERE table_name=%s"
            cur.execute(SQL(query), (table,))
            result = cur.fetchone()
            count = result[0] if result else 0
    connection.close()
    return count > 0


##
