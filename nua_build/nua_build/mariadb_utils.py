"""Nua mariadb runtime related commands.
"""
import os
from pathlib import Path

import mariadb

from .exec import exec_as_root

NUA_MARIADB_PWD_FILE = ".mariadb_pwd"  # noqa S105


def mariadb_pwd() -> str:
    """Return the 'root' user DB password of mariadb.
      - When used in container context, the env variable NUA_MARIADB_PASSWORD should
        contain the password.
      - When used in nua-orchestrator context, read the password from local file.

    For orchestrator context, assuming this function can only be used *after* password
    was generated (or its another bug).

    Rem.: No cache. Rarely used function and pwd can be changed."""
    pwd = os.environ.get("MARIADB_ROOT_PASSWORD")
    if pwd:
        return pwd
    pwd = os.environ.get("NUA_MARIADB_PASSWORD")
    if pwd:
        return pwd
    file_path = Path(os.path.expanduser("~nua")) / NUA_MARIADB_PWD_FILE
    return file_path.read_text(encoding="utf8").strip()


def mariadb_setup_db_user(host: str, dbname: str, user: str, password: str):
    """Create a mariadb user if needed."""
    if not mariadb_user_exist(host, user):
        mariadb_user_create(host, user, password)
    if not mariadb_db_exist(host, dbname):
        mariadb_db_create(host, dbname, user, password)


def mariadb_remove_db_user(host: str, dbname: str, user: str):
    """Remove a mariadb user if needed."""
    if mariadb_db_exist(host, dbname):
        mariadb_db_drop(host, dbname)
    if mariadb_user_exist(host, user):
        mariadb_user_drop(host, user)


def mariadb_db_drop(host: str, dbname: str):
    """Basic drop database."""
    connection = mariadb.connect(host=host, user="root", password=mariadb_pwd())
    cursor = connection.cursor()
    query = f"drop database if exists {dbname}"
    cursor.execute(query)
    connection.close()


def mariadb_db_dump(dbname: str, options_str: str = ""):
    """Basic mariadb_dump call.

    FIXME: not ok for remote host
    """
    cmd = f"mariadb-dump {dbname} {options_str}"
    exec_as_root(cmd)


def mariadb_user_drop(host: str, user: str) -> bool:
    """Drop user (wip, not enough)."""
    connection = mariadb.connect(host=host, user="root", password=mariadb_pwd())
    cursor = connection.cursor()
    query = "DROP USER IF EXISTS ?"
    cursor.execute(query, (user,))
    connection.close()


def mariadb_user_exist(host: str, user: str) -> bool:
    """Test if a mariadb user exists."""
    connection = mariadb.connect(host=host, user="root", password=mariadb_pwd())
    cursor = connection.cursor()
    query = "SELECT EXISTS(SELECT 1 FROM mysql.user WHERE user = ?)"  # noqa S608
    cursor.execute(query, (user,))
    (count,) = cursor.fetchone()
    connection.close()
    return count != 0


def mariadb_user_create(host: str, user: str, password: str):
    """Create a mariadb user.

    Assuming standard port 3306
    """
    connection = mariadb.connect(host=host, user="root", password=mariadb_pwd())
    cursor = connection.cursor()
    query = "CREATE USER IF NOT EXISTS ? IDENTIFIED BY ?"
    cursor.execute(query, (user, password))
    connection.commit()
    connection.close()


def mariadb_db_create(host: str, dbname: str, user: str, password: str):
    """Create a mariadb DB.

    Assuming standard port 3306
    """
    connection = mariadb.connect(host=host, user="root", password=mariadb_pwd())
    cursor = connection.cursor()
    query = f"CREATE DATABASE {dbname}"
    cursor.execute(query)
    # query = f"GRANT ALL PRIVILEGES ON {dbname}.* TO '{user}'@'%' IDENTIFIED BY ?"
    query = f"GRANT ALL PRIVILEGES ON {dbname}.* TO ? IDENTIFIED BY ?"
    cursor.execute(query, (user, password))
    connection.commit()
    connection.close()


def mariadb_db_exist(host: str, dbname: str) -> bool:
    """Test if the named mariadb database exists."""
    connection = mariadb.connect(host=host, user="root", password=mariadb_pwd())
    cursor = connection.cursor()
    query = f"SHOW DATABASES LIKE '{dbname}'"
    cursor.execute(query, (dbname,))
    result = cursor.fetchone()
    connection.close()
    return bool(result)


def mariadb_db_table_exist(
    host: str, dbname: str, user: str, password: str, table: str
) -> bool:
    """Check if the named database exists (for host, connecting as user), assuming
    DB exists."""
    connection = mariadb.connect(
        host=host, database=dbname, user=user, password=password
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
