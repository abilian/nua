"""
Common interface for databases : MariaDB interface
"""
# pyright: reportOptionalCall=false
# pyright: reportOptionalMemberAccess=false
import importlib
import os
from datetime import datetime, timezone
from pathlib import Path
from time import sleep, time

from nua.lib.actions import python_package_installed
from nua.lib.exec import exec_as_root

from .db_manager import DbManager

if python_package_installed("mariadb"):
    mariadb = importlib.import_module("mariadb")
else:
    mariadb = None  # type:ignore

NUA_MARIADB_PWD_FILE = ".mariadb_pwd"  # noqa S105


class MariaDbManager(DbManager):
    """Database manager for MariaDB."""

    def __init__(
        self,
        host: str = "",
        port: str | int = "",
        user: str = "",
        password: str | None = None,
    ):
        if not mariadb:
            raise ValueError("The package 'mariadb' is not installed.")
        self.host = host or "localhost"
        self.port = int(port or "3306")
        self.user = user or "root"
        if password:
            self.password = password
        else:
            self.password = self.mariadb_pwd()

    def root_connect(self):
        return mariadb.connect(
            host=self.host, port=self.port, user=self.user, password=self.password
        )

    def mariadb_pwd(self) -> str:
        """Return the 'root' user DB password of mariadb.

        - container context: the env variable NUA_MARIADB_PASSWORD should contain
        the password.
        """
        pwd = os.environ.get("MARIADB_ROOT_PASSWORD")
        if not pwd:
            pwd = os.environ.get("MYSQL_ROOT_PASSWORD")
        if not pwd:
            pwd = os.environ.get("NUA_MARIADB_PASSWORD")
        if pwd:
            return pwd
        file_path = Path(os.path.expanduser("~nua")) / NUA_MARIADB_PWD_FILE
        return file_path.read_text(encoding="utf8").strip()

    def setup_db_user(self, dbname: str, user: str, password: str):
        """Create a mariadb user if needed."""
        if not self.user_exist(user):
            self.user_create(user, password)
        if not self.db_exist(dbname):
            self.db_create(dbname, user, password)

    def remove_db_user(self, dbname: str, user: str):
        """Remove a mariadb user and DB if needed."""
        if self.db_exist(dbname):
            self.db_drop(dbname)
        if self.user_exist(user):
            self.user_drop(user)

    def db_drop(self, dbname: str):
        """Basic drop database."""
        connection = self.root_connect()
        cursor = connection.cursor()
        query = f"drop database if exists {dbname}"
        cursor.execute(query)
        connection.close()

    def db_dump(self, dbname: str, **kwargs: str):
        """Basic mariadb_dump call.

        FIXME: not ok for remote host
        """
        options = kwargs.get("options", "")
        cmd = f"mariadb-dump {dbname} {options}"
        exec_as_root(cmd)

    def wait_for_db(self, timeout: int = 120):
        """Wait for the DB beeing up."""
        when = time()
        limit = when + timeout
        while time() < limit:
            while time() < when:
                sleep(0.1)
            try:
                self.root_connect()
                now = datetime.now(timezone.utc).isoformat(" ")
                print(f"{now} - Connection ok")
                return
            except mariadb.Error:
                now = datetime.now(timezone.utc).isoformat(" ")
                print(f"{now} - Connection failed")
                when += 5.0
        raise RuntimeError(f"DB not available after {timeout} seconds.")

    def user_drop(self, user: str) -> bool:
        """Drop user (wip, not enough)."""
        connection = self.root_connect()
        cursor = connection.cursor()
        query = "DROP USER IF EXISTS ?"
        cursor.execute(query, (user,))
        connection.close()
        return True

    def user_exist(self, user: str) -> bool:
        """Test if a mariadb user exists."""
        connection = self.root_connect()
        cursor = connection.cursor()
        query = "SELECT EXISTS(SELECT 1 FROM mysql.user WHERE user = ?)"  # noqa S608
        cursor.execute(query, (user,))
        (count,) = cursor.fetchone()
        connection.close()
        return count != 0

    def user_create(self, user: str, password: str):
        """Create a mariadb user."""
        connection = self.root_connect()
        cursor = connection.cursor()
        query = "CREATE USER IF NOT EXISTS ? IDENTIFIED BY ?"
        cursor.execute(query, (user, password))
        connection.commit()
        connection.close()

    def db_exist(self, dbname: str) -> bool:
        """Test if the named mariadb database exists."""
        connection = self.root_connect()
        cursor = connection.cursor()
        query = f"SHOW DATABASES LIKE '{dbname}'"
        cursor.execute(query, (dbname,))
        result = cursor.fetchone()
        connection.close()
        return bool(result)

    def db_create(self, dbname: str, user: str, password: str | None = None):
        """Create a mariadb DB."""
        connection = self.root_connect()
        cursor = connection.cursor()
        query = f"CREATE DATABASE {dbname}"
        cursor.execute(query)
        # query = f"GRANT ALL PRIVILEGES ON {dbname}.* TO '{user}'@'%' IDENTIFIED BY ?"
        query = f"GRANT ALL PRIVILEGES ON {dbname}.* TO ? IDENTIFIED BY ?"
        cursor.execute(query, (user, password))
        connection.commit()
        connection.close()

    def db_table_exist(self, dbname: str, user: str, password: str, table: str) -> bool:
        """Check if the named database exists (for host, connecting as user),
        assuming DB exists."""
        connection = mariadb.connect(
            host=self.host, database=dbname, user=user, password=password
        )
        cursor = connection.cursor()
        query = (
            "SELECT count(*) FROM information_schema.TABLES WHERE "
            f"(TABLE_SCHEMA = '{dbname}') AND (TABLE_NAME = '{table}')"
        )
        # cursor.execute(query, (dbname, table))
        cursor.execute(query)
        result = cursor.fetchone()
        count = result[0] if result else 0
        connection.close()
        return count > 0
