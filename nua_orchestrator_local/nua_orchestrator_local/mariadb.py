"""Nua mariadb related commands.

WIP
"""
import functools
import os
import re
from pathlib import Path

from .actions import install_package_list, installed_packages
from .exec import exec_as_root
from .gen_password import gen_password
from .rich_console import print_magenta, print_red
from .shell import chown_r, sh

MARIADB_VERSION = "10.6"
POSTGRES_CONF_PATH = Path("/todo/etc/postgresql/14/main")
# RE_ANY_PG = re.compile(r"^postgresql-[0-9\.]+/")
RE_PORT = re.compile(r"\s*port\s*=\s*(\d+)")
RE_COMMENT = re.compile(r"\s*#")

RE_LISTEN = re.compile(r"\s*listen_addresses\s*=(.*)$")

# # S105 Possible hardcoded password
NUA_MARIADB_PWD_FILE = ".mariadb_pwd"  # noqa S105


def mariadb_pwd() -> str:
    """Return the 'root' user DB password of mariadb.
      - When used in container context, the env variable NUA_MARIADB_PASSWORD should
        contain the password.
      - When used in nua-orchestrator context, read the password from local file.

    For orchestrator context, assuming this function can only be used *after* password
    was generated (or its another bug).

    Rem.: No cache. Rarely used function and pwd can be changed."""
    pwd = os.environ.get("NUA_MARIADB_PASSWORD")
    if pwd:
        return pwd
    file_path = Path(os.path.expanduser("~nua")) / NUA_MARIADB_PWD_FILE
    return file_path.read_text(encoding="utf8").strip()


def set_random_mariadb_pwd() -> bool:
    print_magenta("Setting Mariadb password")
    return set_mariadb_pwd(gen_password())


def _store_mariadb_password(password: str):
    """Store the password in "~nua/.mariadb_pwd".

    Expect to be run either by root or nua.
    """
    file_path = Path(os.path.expanduser("~nua")) / NUA_MARIADB_PWD_FILE
    file_path.write_text(f"{password}\n", encoding="utf8")
    chown_r(file_path, "nua")
    os.chmod(file_path, 0o600)  # noqa: S103


def set_mariadb_pwd(password: str) -> bool:
    """Set mariadb root password for local instance of mariadb.

    The password is stored in clear in Nua home. In future version, it could be
    replaced by SSL key, thus gaining the ability to have encyption of streams and
    expiration date.
    Basically we need clear password somewhere. Since this password is only used
    by Nua scripts (if Nua is the only user of local mariadb DB), it could also be
    generated / erased at each invocation.
    No test of min password length in this function.
    """
    r_pwd = repr(password)
    exec_as_root("systemctl stop mariadb")
    exec_as_root("mariadbd-safe --skip-grant-tables --skip-networking &")
    cmd = (
        'mariadb -u root  -e "FLUSH PRIVILEGES; '
        f"ALTER USER 'root'@'localhost' IDENTIFIED BY {r_pwd};\""
    )
    exec_as_root(cmd)
    exec_as_root("kill $(cat /run/mysqld/mysqld.pid)")
    exec_as_root("systemctl start mariadb")
    _store_mariadb_password(password)
    print(mariadb_status(password))
    return True


def mariadb_status(password: str) -> str:
    cmd = f"mariadb -u root -p{password} -e 'status'"
    return sh(cmd, capture_output=True)


def mariadb_version() -> str:
    cmd = "mariadb --version"
    line = sh(cmd, capture_output=True)
    parts = line.split()
    if len(parts) > 3 and parts[0] == "mariadb" and parts[3] == "Distrib":
        return parts[4]
    return ""


def mariadb_run_environment(_unused: dict) -> dict:
    """Return a dict of environ variable for docker.run().

    Actually, returns the DB mariadb password.
    This function to be used in orchestrator environment, thus the password will
    be read from host file.
    """
    return {"NUA_MARIADB_PASSWORD": mariadb_pwd()}


def bootstrap_install_mariadb() -> bool:
    """Installing the requied mariadb version locally.

    Need to be executed as root at nua install stage
    """
    print_magenta(f"Installation of mariadb version {MARIADB_VERSION}")
    # detect prior installation of other versions:
    if not _mariadb_verify_no_prior_installation():
        return False
    install_package_list(f"mariadb-server-{MARIADB_VERSION}")
    allow_docker_connection()
    return mariadb_check_installed()


def _mariadb_verify_no_prior_installation() -> bool:
    conf_path = Path("/etc/mysql/mariadb.cnf")
    if not conf_path.is_file():
        return True
    existing_version = mariadb_version()
    if existing_version.startswith(MARIADB_VERSION):
        return True
    print_red(
        "Some Mariadb installation was found and need to be removed by commands like:"
    )
    print_red("    apt purge -y mariadb-server")
    print_red("    apt autoremove -y")
    return False


def mariadb_check_installed() -> bool:
    """Check that mariadb is installed locally."""
    test = _mariadb_check_installed_version()
    if test:
        test = _mariadb_check_std_port()
    return test
    # ensure db started
    # sudo systemctl start postgresql


def _mariadb_check_installed_version() -> bool:
    package = f"mariadb-server-{MARIADB_VERSION}/"
    found = [s for s in installed_packages() if s.startswith(package)]
    if not found:
        print_red(f"Required package not installed: {package}")
        return False
    return True


def _mariadb_check_config_port(path: Path) -> str:
    with open(path, "r", encoding="utf8") as rfile:
        for line in rfile:
            if RE_COMMENT.match(line):
                continue
            if (port_match := RE_PORT.match(line)) is not None:
                return port_match[1].strip()
    return ""


def _mariadb_check_std_port() -> bool:
    path = Path("/etc/mysql/mariadb.cnf")
    if not path.is_file():
        print_red(f"Mariadb config file not found: {path}")
        return False
    port = _mariadb_check_config_port(path)
    if port == "3306" or not port:
        # assuming use of default port of 3306
        return True
    print_red("Mariadb is expected on standard port 3306, check configuration.")
    return False


@functools.cache
def mariadb_check_listening(gateway: str) -> bool:
    """TODO

    heck at deploy time that the postgres daemon is listening on the gateway port
    of the docker service (ip passed as parameter).

    This is launched for every deployed image (so cached).
    """
    return True

    if not mariadb_check_installed():
        return False
    path = Path("/etc/mysql/mariadb.cnf")
    if not path.is_file():
        print_red(f"Mariadb config file not found: {path}")
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
    """
    TODO

    Check at deploy time that the pg_hba.conf file permit connexion.

    Must be run as root at bootstrap time.
    """
    return

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
    """
    TODO

    """
    return
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


def mariadb_restart_service():
    """Restart mariadb service."""
    cmd = "sudo systemctl restart mariadb"
    sh(cmd)


#
# def pg_setup_db_user(host: str, dbname: str, user: str, password: str):
#     """Create a postgres user if needed."""
#     if not pg_user_exist(host, user):
#         pg_user_create(host, user, password)
#     if not pg_db_exist(host, dbname):
#         pg_db_create(host, dbname, user)
#
#
# def pg_remove_db_user(host: str, dbname: str, user: str):
#     """Remove a postgres user if needed."""
#     if pg_db_exist(host, dbname):
#         pg_db_drop(host, dbname)
#     if pg_user_exist(host, user):
#         pg_user_drop(host, user)
#
#
# def pg_db_drop(host: str, dbname: str):
#     """Basic drop database.
#
#     See pg_remove_db_user
#     """
#     connection = psycopg2.connect(
#         dbname="postgres", user="postgres", host=host, password=postgres_pwd()
#     )
#     connection.autocommit = True
#     with connection:
#         with connection.cursor() as cur:
#             query = "REVOKE CONNECT ON DATABASE {db} FROM public"
#             cur.execute(SQL(query).format(db=Identifier(dbname)))
#         with connection.cursor() as cur:
#             query = "DROP DATABASE {db}"
#             cur.execute(SQL(query).format(db=Identifier(dbname)))
#     connection.close()
#
#
# def pg_db_dump(dbname: str, options_str: str = ""):
#     """Basic pg_dump call.
#
#     FIXME: not ok for remote host
#     """
#     cmd = f"pg_dump {dbname} {options_str}"
#     mp_exec_as_postgres(cmd)
#
#
# def pg_user_drop(host: str, user: str) -> bool:
#     """Drop user (wip, not enough)."""
#     connection = psycopg2.connect(host=host, user="postgres", password=postgres_pwd())
#     connection.autocommit = True
#     with connection:  # noqa SIM117
#         with connection.cursor() as cur:
#             query = "DROP USER IF EXISTS {username}"
#             cur.execute(SQL(query).format(username=Identifier(user)))
#     connection.close()
#
#
# def pg_user_exist(host: str, user: str) -> bool:
#     """Test if a postgres user exists."""
#     connection = psycopg2.connect(host=host, user="postgres", password=postgres_pwd())
#     connection.autocommit = True
#     with connection:  # noqa SIM117
#         with connection.cursor() as cur:
#             query = "SELECT COUNT(*) FROM pg_catalog.pg_roles WHERE rolname = %s"
#             cur.execute(SQL(query), (user,))
#             (count,) = cur.fetchone()
#     connection.close()
#     return count != 0
#
#
# def pg_user_create(host: str, user: str, password: str):
#     """Create a postgres user.
#
#     Assuming standard port == 5432
#     """
#     connection = psycopg2.connect(host=host, user="postgres", password=postgres_pwd())
#     with connection:  # noqa SIM117
#         with connection.cursor() as cur:
#             # or:  CREATE USER user WITH ENCRYPTED PASSWORD 'pwd'
#             query = "CREATE ROLE {username} LOGIN PASSWORD %s"
#             cur.execute(SQL(query).format(username=Identifier(user)), (password,))
#             cur.execute("COMMIT")
#     connection.close()
#
#
# def pg_db_create(host: str, dbname: str, user: str):
#     """Create a postgres DB.
#
#     Assuming standard port == 5432
#     """
#     connection = psycopg2.connect(
#         host=host, dbname="postgres", user="postgres", password=postgres_pwd()
#     )
#     connection.autocommit = True
#     cur = connection.cursor()
#     query = "CREATE DATABASE {db} OWNER {user}"
#     cur.execute(SQL(query).format(db=Identifier(dbname), user=Identifier(user)))
#     connection.close()
#     connection = psycopg2.connect(
#         host=host, dbname="postgres", user="postgres", password=postgres_pwd()
#     )
#     connection.autocommit = True
#     with connection:  # noqa SIM117
#         with connection.cursor() as cur:
#             # not this: WITH GRANT OPTION;"
#             query = "GRANT ALL PRIVILEGES ON DATABASE {db} TO {user}"
#             cur.execute(SQL(query).format(db=Identifier(dbname), user=Identifier(user)))
#     connection.close()
#
#
# def pg_db_exist(host: str, dbname: str) -> bool:
#     "Test if the named postgres database exists."
#     connection = psycopg2.connect(
#         host=host, dbname="postgres", user="postgres", password=postgres_pwd()
#     )
#     connection.autocommit = True
#     with connection:  # noqa SIM117
#         with connection.cursor() as cur:
#             query = "SELECT datname FROM pg_database"
#             cur.execute(SQL(query))
#             results = cur.fetchall()
#     connection.close()
#     db_set = {x[0] for x in results if x}
#     return dbname in db_set
#
#
# def pg_db_table_exist(
#     host: str, dbname: str, user: str, password: str, table: str
# ) -> bool:
#     """Check if the named database exists (for host, connecting as user), assuming
#     DB exists."""
#     connection = psycopg2.connect(
#         host=host, dbname=dbname, user=user, password=password
#     )
#     with connection:  # noqa SIM117
#         with connection.cursor() as cur:
#             query = "SELECT COUNT(*) FROM information_schema.tables WHERE table_name=%s"
#             cur.execute(SQL(query), (table,))
#             result = cur.fetchone()
#             count = result[0] if result else 0
#     connection.close()
#     return count > 0
