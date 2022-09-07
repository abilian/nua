"""Nua postgresql related commands."""
import re
from pathlib import Path

import psycopg2
from psycopg2 import sql

from .actions import install_package_list, installed_packages
from .exec import mp_exec_as_postgres
from .rich_console import print_magenta, print_red

PG_VERSION = "14"
RE_ANY_PG = re.compile(r"^postgresql-[0-9\.]+/")
RE_5432 = re.compile(r"\s*port\s*=\s*5432\D")


def postgres_pwd() -> str:
    """See later how to get the postgres password of postgres user."""
    return "the_pass"


def set_postgres_pwd():
    """See later how to get the postgres password of postgres user."""
    print_magenta("Setting Postgres password")
    orig_passwd = "the_pass"  # FIXME, of course.
    # i_pwd = sql.Identifier(orig_passwd)
    r_pwd = repr(orig_passwd)
    # query = sql.SQL("ALTER USER postgres PASSWORD {}".format(i_pwd))
    query = f"ALTER USER postgres PASSWORD {r_pwd}"
    cmd = ["psql", "-c", query]
    mp_exec_as_postgres(cmd)
    return True


def bootstrap_install_postgres() -> bool:
    """Installing the requied Postgres version.

    Need to be executed as root at nua install stage"""
    print_magenta(f"Installation of postgres version {PG_VERSION}")
    # detect prior installation of other versions:
    if not _pg_verify_no_prior_installation():
        return False
    install_package_list([f"postgresql-{PG_VERSION}"])
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
    conf_path = Path(f"/etc/postgresql/{PG_VERSION}/main/postgresql.conf")
    if not conf_path.is_file():
        print_red(f"Postgres config file not found: {conf_path}")
        return False
    with open(conf_path, "r", encoding="utf8") as rfile:
        for line in rfile:
            if RE_5432.match(line):
                return True
    print_red("Postgres is expected on standard port 5432, check configuration.")
    return False


def pg_setup_db_user(dbname: str, user: str, password: str):
    if not pg_user_exist(user):
        pg_user_create(user, password)
    if not pg_db_exist(dbname):
        pg_db_create(dbname, user)


def pg_remove_db_user(dbname: str, user: str):
    if pg_db_exist(dbname):
        pg_db_drop(dbname)
    if pg_user_exist(user):
        pg_user_drop(user)


def pg_db_drop(dbname: str):
    """Basic drop database. See pg_remove_db_user"""
    connection = psycopg2.connect(
        dbname="postgres", user="postgres", host="localhost", password=postgres_pwd()
    )
    connection.autocommit = True
    db = sql.Identifier(dbname)
    with connection:
        with connection.cursor() as cur:
            query = sql.SQL(f"REVOKE CONNECT ON DATABASE {db} FROM public;")
            cur.execute(sql.SQL(query))
        with connection.cursor() as cur:
            query = sql.SQL(f"DROP DATABASE example {db} ")
            cur.execute(sql.SQL(query))
    connection.close()


def pg_db_dump(dbname: str, options_str: str = ""):
    """Basic pg_dump call."""
    cmd = "pg_dump {dbname} {options_str}"
    mp_exec_as_postgres(cmd)


def pg_user_drop(user: str) -> bool:
    """Drop user (wip, not enough)."""
    connection = psycopg2.connect(
        user="postgres", host="localhost", password=postgres_pwd()
    )
    connection.autocommit = True
    username = sql.Identifier(user)
    query = sql.SQL(f"DROP USER IF EXISTS {username};")
    with connection:
        with connection.cursor() as cur:
            cur.execute(query)
    connection.close()


def pg_user_exist(user: str) -> bool:
    connection = psycopg2.connect(
        user="postgres", host="localhost", password=postgres_pwd()
    )
    connection.autocommit = True
    username = sql.Identifier(user)
    query = sql.SQL(
        f"SELECT COUNT(*) FROM pg_catalog.pg_roles WHERE rolname = {username}"
    )
    with connection:
        with connection.cursor() as cur:
            cur.execute(query)
            (count,) = cur.fetchone()
    connection.close()
    return count != 0


def pg_user_create(user: str, password: str):
    "create user. Assuming std port of 5432"

    connection = psycopg2.connect(
        user="postgres", host="localhost", password=postgres_pwd()
    )
    username = sql.Identifier(user)
    passwd = sql.Literal(password)
    query = sql.SQL(f"CREATE ROLE {username} LOGIN PASSWORD {passwd}")
    # CREATE USER user WITH ENCRYPTED PASSWORD 'pwd'
    with connection:
        with connection.cursor() as cur:
            cur.execute(query)
            cur.execute("COMMIT")
    connection.close()


def pg_db_create(name: str, user: str):
    "create db. Assuming std port of 5432"

    connection = psycopg2.connect(
        dbname="postgres", user="postgres", host="localhost", password=postgres_pwd()
    )
    connection.autocommit = True
    with connection:
        with connection.cursor() as cur:
            db = sql.Identifier(name)
            user = sql.Identifier(user)
            cur.execute(
                sql.SQL(
                    f"CREATE DATABASE {db} OWNER {user}; "
                    f"GRANT ALL PRIVILEGES ON DATABASE ${db} TO ${user}"
                    # WITH GRANT OPTION;"
                )
            )
    connection.close()


def pg_db_exist(dbname: str) -> bool:
    "Check if the named database exists (locally)."
    connection = psycopg2.connect(
        dbname="postgres", user="postgres", host="localhost", password=postgres_pwd()
    )
    connection.autocommit = True
    with connection:
        with connection.cursor() as cur:
            cur.execute("SELECT datname FROM pg_database;")
            db_list = cur.fetchall()
    return dbname in db_list
