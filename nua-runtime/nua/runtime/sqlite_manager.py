"""
Common interface for databases : SQLite3 interface
"""
import sqlite3
from pathlib import Path

from nua.lib.tool.state import verbosity

from .db_manager import DbManager


class SQLiteManager(DbManager):
    """Database manager for SQLite3."""

    def __init__(self, host: str, port: str, user: str, password: str):
        """No actual init required for SQLite3."""
        pass

    def setup_db_user(self, dbname: str, user: str, password: str):
        pass

    def remove_db_user(self, dbname: str, user: str):
        pass

    def db_drop(self, dbname: str):
        if dbname == ":memory:":
            return
        Path(dbname).unlink()

    def db_dump(self, dbname: str, *kwargs: str):
        if not self.db_exist(dbname):
            return False
        dest_file = kwargs.get("output")
        if not dest_file:
            raise ValueError("Missing 'output' destination file.")
        connection = sqlite3.connect(dbname)
        with open(dest_file, "w") as wfile:
            for line in connection.iterdump():
                f.write("{line}\n")
        connection.close()

    def user_drop(self, user: str) -> bool:
        pass

    def user_exist(self, user: str) -> bool:
        pass

    def user_create(self, user: str, password: str):
        pass

    def db_exist(self, dbname: str) -> bool:
        return Path(dbname).is_file()

    def db_create(self, dbname: str, user: str):
        conn = sqlite3.connect(dbname)
        if verbosity(2):
            print(f"SQLite DB {dbname} created.")

    def db_table_exist(self, dbname: str, user: str, password: str, table: str) -> bool:
        if not self.db_exist(dbname):
            return False
        connection = sqlite3.connect(dbname)
        cursor = connection.cursor()
        table_list = cursor.execute(
            """SELECT name FROM sqlite_master WHERE type='table'
           AND name='{tale}'; """
        ).fetchall()
        connection.commit()
        connection.close()
        return bool(table_list)
