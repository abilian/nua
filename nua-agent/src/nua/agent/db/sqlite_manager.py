"""
Common interface for databases : SQLite3 interface
"""
import sqlite3
from pathlib import Path

from nua.lib.panic import vprint
from nua.lib.tool.state import verbosity

from .db_manager import DbManager


class SQLiteManager(DbManager):
    """Database manager for SQLite3."""

    def __init__(self, host: str, port: str, user: str, password: str):
        """No actual init required for SQLite3."""
        return

    def setup_db_user(self, dbname: str, user: str, password: str):
        return

    def remove_db_user(self, dbname: str, user: str):
        return

    def db_drop(self, dbname: str):
        if dbname == ":memory:":
            return
        Path(dbname).unlink()

    def db_dump(self, dbname: str, **kwargs: str):
        if not self.db_exist(dbname):
            raise ValueError(f"Sqlite database {dbname} doesn't exist.")
        dest_file = kwargs.get("output")
        if not dest_file:
            raise ValueError("Missing 'output' destination file.")
        connection = sqlite3.connect(dbname)
        with open(dest_file, "w") as wfile:
            for line in connection.iterdump():
                wfile.write(f"{line}\n")
        connection.close()

    def user_drop(self, user: str) -> bool:
        return True

    def user_exist(self, user: str) -> bool:
        return True

    def user_create(self, user: str, password: str):
        return

    def db_exist(self, dbname: str) -> bool:
        return Path(dbname).is_file()

    def db_create(self, dbname: str, user: str, _password: str | None = None):
        connection = sqlite3.connect(dbname)
        with verbosity(2):
            vprint(f"SQLite DB {dbname} created.")
        connection.close()

    def db_table_exist(self, dbname: str, user: str, password: str, table: str) -> bool:
        if not self.db_exist(dbname):
            return False
        connection = sqlite3.connect(dbname)
        cursor = connection.cursor()
        table_list = cursor.execute(
            """
            SELECT name FROM sqlite_master WHERE type='table' AND name='{tale}';
            """
        ).fetchall()
        connection.commit()
        connection.close()
        return bool(table_list)
