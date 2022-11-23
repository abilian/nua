"""Example adapted from:
https://www.digitalocean.com/community/tutorials/
    how-to-use-a-postgresql-database-in-a-flask-application"""

import os

import mariadb
from flask_mariadb_docker_wheel.constants import (
    DB_HOST,
    DB_PORT,
    USER_DB,
    USER_NAME,
    USER_PASSWORD,
)
from nua.lib.exec import exec_as_root

# Nua shortcuts to manage mariadb:
from nua.runtime.mariadb_manager import MariaDbManager


def setup_db():
    """Find or create the required DB.

    In this example The DB is manage by a dedicated docker container."""
    manager = MariaDbManager(DB_HOST, DB_PORT, "", "")
    manager.setup_db_user(USER_DB, USER_NAME, USER_PASSWORD)


def init_db_content():
    manager = MariaDbManager(DB_HOST, DB_PORT, "", "")
    if not manager.db_table_exist(
        USER_DB,
        USER_NAME,
        USER_PASSWORD,
        "books",
    ):
        add_content()


def add_content():
    connection = mariadb.connect(
        host=DB_HOST,
        database=USER_DB,
        user=USER_NAME,
        password=USER_PASSWORD,
    )
    cursor = connection.cursor()
    cursor.execute("DROP TABLE IF EXISTS books")
    connection.commit()
    cursor.execute(
        "create TABLE books (id serial PRIMARY KEY,"
        "title varchar (150) NOT NULL,"
        "author varchar (50) NOT NULL,"
        "pages_num integer NOT NULL,"
        "review text,"
        "date_added timestamp DEFAULT CURRENT_TIMESTAMP)"
    )
    # Insert data into the table
    cursor.execute(
        "INSERT INTO books (title, author, pages_num, review) VALUES (?, ?, ?, ?)",
        (
            "A Tale of Two Cities",
            "Charles Dickens",
            489,
            "A great classic!",
        ),
    )
    cursor.execute(
        "INSERT INTO books (title, author, pages_num, review) VALUES (?, ?, ?, ?)",
        ("Anna Karenina", "Leo Tolstoy", 864, "Another great classic!"),
    )
    connection.commit()
    connection.close()


setup_db()
init_db_content()

cmd = "gunicorn --worker-tmp-dir /dev/shm --workers 2 -b :80 flask_mariadb_docker_wheel.wsgi:app"
# exec_as_nua(cmd, env)
# We need to exec as root to be able to write files in the docker volume.
exec_as_root(cmd, env=os.environ)
