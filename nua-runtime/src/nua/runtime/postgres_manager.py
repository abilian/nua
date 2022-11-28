"""
Common interface for databases : Postgres interface

Todo: separate part for local/remote instance
"""
# pyright: reportOptionalCall=false
# pyright: reportOptionalMemberAccess=false
import importlib
import os
import re
from pathlib import Path

from nua.lib.exec import mp_exec_as_postgres

from .db_manager import DbManager
from .utils import is_package_installed

if is_package_installed("psycopg2"):
    psycopg2 = importlib.import_module("psycopg2")
    SQL = getattr(importlib.import_module("psycopg2.sql"), "SQL")  # noqa B009
    Identifier = getattr(  # noqa B009
        importlib.import_module("psycopg2.sql"), "Identifier"
    )
else:
    psycopg2 = None  # type: ignore
    SQL = None
    Identifier = None

PG_VERSION = "14"
POSTGRES_CONF_PATH = Path(f"/etc/postgresql/{PG_VERSION}/main")
RE_ANY_PG = re.compile(r"^postgresql-[0-9\.]+/")
RE_5432 = re.compile(r"\s*port\s*=\s*5432\D")
RE_COMMENT = re.compile(r"\s*#")
RE_LISTEN = re.compile(r"\s*listen_addresses\s*=(.*)$")
# S105 Possible hardcoded password
NUA_PG_PWD_FILE = ".postgres_pwd"  # noqa S105


class PostgresManager(DbManager):
    """Database manager for Postgres."""

    def __init__(self, host: str, port: str, user: str, password: str):
        if not psycopg2:
            raise ValueError("The package 'postgres' is not installed.")
        self.host = host or "localhost"
        self.port = int(port or "5432")
        self.user = user or "postgres"
        if password:
            self.password = password
        else:
            self.password = self.postgres_pwd()

    def root_connect(self):
        return psycopg2.connect(
            host=self.host,
            port=self.port,
            dbname="postgres",
            user=self.user,
            password=self.password,
        )

    def postgres_pwd(self) -> str:
        """Return the 'postgres' user DB password.

        - When used in container context, the env variable POSTGRES_PASSWORD or
          NUA_POSTGRES_PASSWORD should contain the password.
        - When used in nua-orchestrator context, read the password from local file.
        """
        pwd = os.environ.get("POSTGRES_PASSWORD")
        if pwd:
            # it the common environ variable for postgres docker image
            return pwd
        pwd = os.environ.get("NUA_POSTGRES_PASSWORD")
        if pwd:
            return pwd
        file_path = Path(os.path.expanduser("~nua")) / NUA_PG_PWD_FILE
        with open(file_path, encoding="utf8") as rfile:
            pwd = rfile.read().strip()
        return pwd

    def setup_db_user(self, dbname: str, user: str, password: str):
        """Create a postgres user if needed."""
        if not self.user_exist(user):
            self.user_create(user, password)
        if not self.db_exist(dbname):
            self.db_create(dbname, user)

    def remove_db_user(self, dbname: str, user: str):
        """Remove a postgres user and DB if needed."""
        if self.db_exist(dbname):
            self.db_drop(dbname)
        if self.user_exist(user):
            self.user_drop(user)

    def db_drop(self, dbname: str):
        """Basic drop database."""
        connection = self.root_connect()
        connection.autocommit = True
        with connection:
            with connection.cursor() as cur:
                query = "REVOKE CONNECT ON DATABASE {db} FROM public"
                cur.execute(SQL(query).format(db=Identifier(dbname)))
            with connection.cursor() as cur:
                query = "DROP DATABASE {db}"
                cur.execute(SQL(query).format(db=Identifier(dbname)))
        connection.close()  # <- Needed? The with statement should close it.

    def db_dump(self, dbname: str, **kwargs: str):
        """Basic pg_dump call.

        FIXME: not ok for remote host
        """
        options = kwargs.get("options", "")
        cmd = f"pg_dump {dbname} {options}"
        mp_exec_as_postgres(cmd)

    def user_drop(self, user: str) -> bool:
        """Drop user (wip, not enough)."""
        connection = self.root_connect()
        connection.autocommit = True
        with connection:  # noqa SIM117
            with connection.cursor() as cur:
                query = "DROP USER IF EXISTS {username}"
                cur.execute(SQL(query).format(username=Identifier(user)))
        connection.close()  # <- Needed? The with statement should close it.
        return True

    def user_exist(self, user: str) -> bool:
        """Test if a postgres user exists."""
        connection = self.root_connect()
        connection.autocommit = True
        with connection:  # noqa SIM117
            with connection.cursor() as cur:
                query = "SELECT COUNT(*) FROM pg_catalog.pg_roles WHERE rolname = %s"
                cur.execute(SQL(query), (user,))
                result = cur.fetchone()
                count = result[0] if result else 0
        connection.close()  # <- Needed? The with statement should close it.
        return count != 0

    def user_create(self, user: str, password: str):
        """Create a postgres user."""
        connection = self.root_connect()
        with connection:  # noqa SIM117
            with connection.cursor() as cur:
                # or:  CREATE USER user WITH ENCRYPTED PASSWORD 'pwd'
                query = "CREATE ROLE {username} LOGIN PASSWORD %s"
                cur.execute(SQL(query).format(username=Identifier(user)), (password,))
                cur.execute("COMMIT")
        connection.close()

    def db_exist(self, dbname: str) -> bool:
        """Test if the named postgres database exists."""
        connection = self.root_connect()
        connection.autocommit = True
        with connection:  # noqa SIM117
            with connection.cursor() as cur:
                query = "SELECT datname FROM pg_database"
                cur.execute(SQL(query))
                results = cur.fetchall()
        connection.close()
        db_set = {x[0] for x in results if x}
        return dbname in db_set

    def db_create(self, dbname: str, user: str, _password: str | None = None):
        """Create a postgres DB.

        (password unused for postgres)
        """
        connection = self.root_connect()
        connection.autocommit = True
        cur = connection.cursor()
        query = "CREATE DATABASE {db} OWNER {user}"
        cur.execute(SQL(query).format(db=Identifier(dbname), user=Identifier(user)))
        connection.close()
        connection = self.root_connect()
        connection.autocommit = True
        with connection:  # noqa SIM117
            with connection.cursor() as cur:
                # not this: WITH GRANT OPTION;"
                query = "GRANT ALL PRIVILEGES ON DATABASE {db} TO {user}"
                cur.execute(
                    SQL(query).format(db=Identifier(dbname), user=Identifier(user))
                )
        connection.close()

    def db_table_exist(self, dbname: str, user: str, password: str, table: str) -> bool:
        """Check if the named database exists (for host, connecting as user),
        assuming DB exists."""
        connection = psycopg2.connect(
            host=self.host, port=self.port, dbname=dbname, user=user, password=password
        )
        with connection:  # noqa SIM117
            with connection.cursor() as cur:
                query = (
                    "SELECT COUNT(*) FROM information_schema.tables WHERE table_name=%s"
                )
                cur.execute(SQL(query), (table,))
                result = cur.fetchone()
                count = result[0] if result else 0
        connection.close()
        return count > 0


# TODO: check if needed in runtime:
#
# def set_random_postgres_pwd() -> bool:
#     print_magenta("Setting Postgres password")
#     return set_postgres_pwd(gen_password(24))
#
#
# def _store_pg_password(password: str):
#     """Store the password in "~nua/.postgres_pwd".
#
#     Expect to be run either by root or nua.
#     """
#     file_path = Path(os.path.expanduser("~nua")) / NUA_PG_PWD_FILE
#     with open(file_path, "w", encoding="utf8") as wfile:
#         wfile.write(f"{password}\n")
#     chown_r(file_path, "nua")
#     os.chmod(file_path, 0o600)  # noqa: S103
#
# def set_postgres_pwd(password: str) -> bool:
#     """Set postgres password for local instance of postgres.
#
#     The password is stored in clear in Nua home. In future version, it could be
#     replaced by SSL key, thus gaining the ability to have encyption of streams and
#     expiration date.
#     Basically we need clear password somewhere. Since this password is only used
#     by Nua scripts (if Nua is the only user of local postgres DB), it could also be
#     generated / erased at each invocation. Passord could be stored in some file in the
#     postgres user home (a postgres feature).
#     No test of min password length in this function.
#     """
#     r_pwd = repr(password)
#     # query = SQL("ALTER USER postgres PASSWORD {}".format(i_pwd))
#     query = f"ALTER USER postgres PASSWORD {r_pwd}"
#     cmd = f'/usr/bin/psql -c "{query}"'
#     mp_exec_as_postgres(cmd, cwd="/tmp", show_cmd=False)  # noqa S108
#     _store_pg_password(password)
#     return True
#
#
# def pg_run_environment(_unused: dict) -> dict:
#     """Return a dict of environ variable for docker.run().
#
#     Actually, returns the DB postges password.
#     This function to be used in orchestrator environment, thus the password will
#     be read from host file.
#     """
#     return {"NUA_POSTGRES_PASSWORD": postgres_pwd()}

#
# def bootstrap_install_postgres() -> bool:
#     """Installing the requied Postgres version locally.
#
#     Need to be executed as root at nua install stage
#     """
#     print_magenta(f"Installation of postgres version {PG_VERSION}")
#     # detect prior installation of other versions:
#     if not _pg_verify_no_prior_installation():
#         return False
#     install_package_list(
#         [f"postgresql-{PG_VERSION}", "libpq-dev"],
#         update=False,
#         clean=False,
#         keep_lists=True,
#     )
#     allow_docker_connection()
#     return pg_check_installed()
#
#
# def _pg_verify_no_prior_installation() -> bool:
#     conf_path = Path("/etc/postgresql")
#     if not conf_path.is_dir():
#         return True
#     existing = [x.name for x in conf_path.iterdir()]
#     bad_version = [x for x in existing if x != PG_VERSION]
#     if not bad_version:
#         return True
#     print_red(
#         "Some Postgres installation was found and need to be removed by commands like:"
#     )
#     for version in bad_version:
#         print_red(f"    apt purge -y postgresql-{version}")
#     print_red("    apt autoremove -y")
#     return False
#
#
# def pg_check_installed() -> bool:
#     """Check that postgres is installed locally."""
#     test = _pg_check_installed_version()
#     if test:
#         test = _pg_check_std_port()
#     return test
#     # ensure db started
#     # sudo systemctl start postgresql
#
#
# def _pg_check_installed_version() -> bool:
#     pg_package = f"postgresql-{PG_VERSION}/"
#     found = [s for s in installed_packages() if s.startswith(pg_package)]
#     if not found:
#         print_red(f"Required package not installed: postgresql-{PG_VERSION}")
#         return False
#     return True
#
#
# def _pg_check_std_port() -> bool:
#     path = POSTGRES_CONF_PATH / "postgresql.conf"
#
#     if not path.is_file():
#         print_red(f"Postgres config file not found: {path}")
#         return False
#
#     with open(path, encoding="utf8") as rfile:
#         for line in rfile:
#             if RE_5432.match(line):
#                 return True
#
#     print_red("Postgres is expected on standard port 5432, check configuration.")
#     return False
#

#
# @functools.cache
# def pg_check_listening(gateway: str) -> bool:
#     """Check at deploy time that the postgres daemon is listening on the gateway port
#     of the docker service (ip passed as parameter).
#
#     This is launched for every deployed image (so cached).
#     """
#     if not pg_check_installed():
#         return False
#     path = POSTGRES_CONF_PATH / "postgresql.conf"
#     if not path.is_file():
#         print_red(f"Postgres config file not found: {path}")
#         return False
#     return _actual_check_listening(gateway, path)
#
#
# def _actual_check_listening(gateway: str, path: Path) -> bool:
#     with open(path, encoding="utf8") as rfile:
#         for line in rfile:
#             if RE_COMMENT.match(line):
#                 continue
#             if (listen_match := RE_LISTEN.match(line)) is not None:
#                 listening = listen_match[1].strip()
#                 return _add_gateway_address(listening, gateway)
#     return _add_gateway_address("", gateway)
#
#
# def allow_docker_connection():
#     """Check at deploy time that the pg_hba.conf file permit connexion.
#
#     Must be run as root at bootstrap time.
#     """
#
#     auth_line = (
#         "host    all             all             172.16.0.0/12           password"
#     )
#
#     path = POSTGRES_CONF_PATH / "pg_hba.conf"
#     if not path.is_file():
#         print_red(f"Postgres config file not found: {path}")
#         return False
#     with open(path, encoding="utf8") as rfile:
#         content = rfile.read()
#     if auth_line in content:
#         return
#
#     with open(path, "a", encoding="utf8") as afile:
#         afile.write(auth_line)
#         afile.write("\n")
#
#
# def _save_config_gateway_address(content: str):
#     src_path = Path("~/nua_listening_docker.conf.tmp").expanduser()
#     with open(src_path, "w", encoding="utf8") as wfile:
#         wfile.write(content)
#     dest_path = POSTGRES_CONF_PATH / "conf.d" / "nua_listening_docker.conf"
#
#     cmd = f"sudo mv -f {src_path} {dest_path}"
#     sh(cmd, show_cmd=False)
#
#     cmd = f"sudo chown postgres:postgres {dest_path}"
#     sh(cmd, show_cmd=False)
#
#     cmd = f"sudo chmod 644 {dest_path}"
#     sh(cmd, show_cmd=False)
#
#
# def _add_gateway_address(listening: str, gateway: str) -> bool:
#     if not listening:
#         content = f"listen_addresses = 'localhost, {gateway}'\n"
#         _save_config_gateway_address(content)
#         return True
#     if gateway in listening or "*" in listening:
#         return True
#     if listening.endswith("'"):
#         value = f"{listening[:-1]}, {gateway}'"
#     elif listening.endswith('"'):
#         value = f'{listening[:-1]}, {gateway}"'
#     else:  # dubious
#         value = f"'{listening}, {gateway}'"
#     content = f"listen_addresses = {value}'\n"
#     _save_config_gateway_address(content)
#     return True
#
#
# def pg_restart_service():
#     """Restart postgres service."""
#     # cmd = "sudo service postgresql restart"
#     cmd = "sudo systemctl restart postgresql"
#     sh(cmd)
