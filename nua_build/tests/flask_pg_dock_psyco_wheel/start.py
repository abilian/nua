"""Example adapted from:
https://www.digitalocean.com/community/tutorials/how-to-use-a-postgresql-database-in-a-flask-application"""

import os

import psycopg2
from flask_pg_dock_psyco.constants import (
    DB_HOST,
    DB_PORT,
    POSTGRES_DB,
    POSTGRES_PASSWORD,
    POSTGRES_USER,
)

from nua_build import postgres  # Nua shortcuts to manage postgres operations
from nua_build.exec import exec_as_root


def setup_db():
    """Find or create the required DB.

    In this example The DB is on remote docker container."""
    postgres.pg_setup_db_user_port(
        host=DB_HOST,
        port=DB_PORT,
        dbname=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
    )


def init_db_content():
    if not postgres.pg_db_table_exist_port(
        host=DB_HOST,
        port=DB_PORT,
        dbname=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        table="books",
    ):
        add_content()


def add_content():
    connection = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
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
