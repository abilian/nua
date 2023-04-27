"""
Common interface for databases : Postgres interface

Todo: separate part for local/remote instance
"""
# pyright: reportOptionalCall=false
# pyright: reportOptionalMemberAccess=false
import importlib
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from time import sleep, time

from nua.lib.actions import python_package_installed
from nua.lib.exec import mp_exec_as_postgres

from .db_manager import DbManager

if python_package_installed("psycopg2") or python_package_installed("psycopg2-binary"):
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
RE_5432 = re.compile(r"\s*port\s*=\s*5432\D")
RE_COMMENT = re.compile(r"\s*#")
RE_LISTEN = re.compile(r"\s*listen_addresses\s*=(.*)$")
# S105 Possible hardcoded password
NUA_PG_PWD_FILE = ".postgres_pwd"  # noqa S105


class PostgresManager(DbManager):
    """Database manager for Postgres."""

    def __init__(
        self,
        host: str = "",
        port: str | int = "",
        user: str = "",
        password: str | None = None,
    ):
        if not psycopg2:
            raise ValueError("The package 'psycopg2' is not installed.")
        self.host = host or "localhost"
        self.port = int(port or "5432")
        self.user = user or "postgres"
        if password:
            self.password = password
        else:
            self.password = self.postgres_pwd()

    def __str__(self) -> str:
        return f"{self.user}@{self.host}:{self.port}"

    def root_connect(self, connect_timeout: int = 5):
        return psycopg2.connect(
            host=self.host,
            port=self.port,
            dbname="postgres",
            user=self.user,
            password=self.password,
            connect_timeout=connect_timeout,
        )

    def postgres_pwd(self) -> str:
        """Return the 'postgres' user DB password.

        - When used in container context, the env variable POSTGRES_PASSWORD or
          NUA_POSTGRES_PASSWORD should contain the password.
        - When used in nua-orchestrator context, read the password from local file.
        """
        pwd = os.environ.get("POSTGRES_PASSWORD")
        if pwd:
            # it is the common environ variable for postgres docker image
            return pwd
        pwd = os.environ.get("NUA_POSTGRES_PASSWORD")
        if pwd:
            return pwd
        file_path = Path("~nua").expanduser() / NUA_PG_PWD_FILE
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

    def wait_for_db(self, timeout: int = 120):
        """Wait for the DB beeing up."""
        when = time()
        limit = when + timeout
        while time() < limit:
            while time() < when:
                sleep(0.1)
            try:
                self.root_connect(connect_timeout=5)
                now = datetime.now(timezone.utc).isoformat(" ")
                print(f"{now} - Connection ok")
                return
            except psycopg2.OperationalError:
                now = datetime.now(timezone.utc).isoformat(" ")
                print(f"{now} - Connection failed")
                when += 5.0
        raise RuntimeError(f"DB not available after {timeout} seconds.")

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
