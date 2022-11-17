"""Example adapted from:
https://www.digitalocean.com/community/tutorials/how-to-use-a-postgresql-database-in-a-flask-application"""
#
# RUN echo "listen_addresses='*'" >> /etc/postgresql/9.3/main/postgresql.conf
# RUN echo "host all  all    0.0.0.0/0  trust" >> /etc/postgresql/9.3/main/pg_hba.conf

import os

import psycopg2
from flask_pg_dock_psyco.constants import (
    DB_HOST,
    DB_PORT,
    POSTGRES_PASSWORD,
    USER_DB,
    USER_NAME,
    USER_PASSWORD,
)
from nua.lib.common.exec import exec_as_root

# Nua shortcuts to manage postgres operations
from nua.runtime.postgres_manager import PostgresManager


def setup_db():
    """Find or create the required DB for app user.

    In this example The DB is on remote docker container."""
    manager = PostgresManager(DB_HOST, DB_PORT, "", "")
    postgres.setup_db_user(
        USER_DB,
        USER_NAME,
        USER_PASSWORD,
    )


def init_db_content():
    manager = PostgresManager(DB_HOST, DB_PORT, "", "")
    if not manager.db_table_exist(
        USER_DB,
        USER_NAME,
        USER_PASSWORD,
        "books",
    ):
        add_content()


def add_content():
    connection = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=USER_DB,
        user=USER_NAME,
        password=USER_PASSWORD,
    )
    with connection:
        with connection.cursor() as cur:
            # Execute a command: this creates a new table
            cur.execute("DROP TABLE IF EXISTS books;")  # ok, this is an example
            cur.execute(
                "CREATE TABLE books (id serial PRIMARY KEY,"
                "title varchar (150) NOT NULL,"
                "author varchar (50) NOT NULL,"
                "pages_num integer NOT NULL,"
                "review text,"
                "date_added date DEFAULT CURRENT_TIMESTAMP);"
            )

            # Insert data into the table

            cur.execute(
                "INSERT INTO books (title, author, pages_num, review)"
                "VALUES (%s, %s, %s, %s)",
                (
                    "A Tale of Two Cities",
                    "Charles Dickens",
                    489,
                    "A great classic!",
                ),
            )

            cur.execute(
                "INSERT INTO books (title, author, pages_num, review)"
                "VALUES (%s, %s, %s, %s)",
                ("Anna Karenina", "Leo Tolstoy", 864, "Another great classic!"),
            )

            connection.commit()
    connection.close()


setup_db()
init_db_content()

cmd = (
    "gunicorn --worker-tmp-dir /dev/shm --workers 2 -b :80 flask_pg_dock_psyco.wsgi:app"
)
# exec_as_nua(cmd, env)
# We need to exec as root to be able to write files in the docker volume.
exec_as_root(cmd, env=os.environ)
