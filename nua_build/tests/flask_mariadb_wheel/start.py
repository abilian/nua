"""Example adapted from:
https://www.digitalocean.com/community/tutorials/
    how-to-use-a-postgresql-database-in-a-flask-application"""

import os

import mariadb
from flask_mariadb_wheel.constants import DB_HOST, DB_NAME, DB_USER, DB_USER_PWD

from nua_build import mariadb_tools as mdb  # Nua shortcuts to manage mariadb
from nua_build.exec import exec_as_root


def setup_db():
    """Find or create the required DB.

    In this example The DB is local to the Host (outside Docker).
    When orchestrator was installed, it must have setup mariadb package on the host."""
    mdb.mariadb_setup_db_user(
        host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_USER_PWD
    )


def init_db_content():
    if not mdb.mariadb_db_table_exist(
        host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_USER_PWD, table="books"
    ):
        add_content()


def add_content():
    connection = mariadb.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_USER_PWD,
    )
    cursor = connection.dursor()
    # Execute a command: this creates a new table
    cursor.execute("DROP TABLE IF EXISTS books;")  # ok, this is an example
    cursor.execute(
        "CREATE TABLE books (id serial PRIMARY KEY,"
        "title varchar (150) NOT NULL,"
        "author varchar (50) NOT NULL,"
        "pages_num integer NOT NULL,"
        "review text,"
        "date_added date DEFAULT CURRENT_TIMESTAMP);"
    )

    # Insert data into the table
    cursor.execute(
        "INSERT INTO books (title, author, pages_num, review)" "VALUES (?, ?, ?, ?)",
        (
            "A Tale of Two Cities",
            "Charles Dickens",
            489,
            "A great classic!",
        ),
    )

    cursor.execute(
        "INSERT INTO books (title, author, pages_num, review)" "VALUES (?, ?, ?, ?)",
        ("Anna Karenina", "Leo Tolstoy", 864, "Another great classic!"),
    )

    connection.close()


setup_db()
init_db_content()

cmd = "gunicorn --worker-tmp-dir /dev/shm --workers 2 -b :80 flask_pg_psyco.wsgi:app"
# exec_as_nua(cmd, env)
# We need to exec as root to be able to write files in the docker volume.
exec_as_root(cmd, env=os.environ)
