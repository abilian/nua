"""Example adapted from:

https://www.digitalocean.com/community/tutorials/
    how-to-use-a-postgresql-database-in-a-flask-application
"""
#
# RUN echo "listen_addresses='*'" >> /etc/postgresql/9.3/main/postgresql.conf
# RUN echo "host all  all    0.0.0.0/0  trust" >> /etc/postgresql/9.3/main/pg_hba.conf

import mariadb
from nua.lib.db.mariadb_manager import MariaDbManager

from .constants import DB_HOST, DB_PORT, USER_DB, USER_NAME, USER_PASSWORD


def init_db():
    wait_for_db()
    load_content()


def wait_for_db():
    manager = MariaDbManager(
        host=DB_HOST,
        port=DB_PORT,
        user=USER_NAME,
        password=USER_PASSWORD,
    )
    manager.wait_for_db()


def load_content():
    manager = MariaDbManager(
        host=DB_HOST,
        port=DB_PORT,
        user=USER_DB,
        password=USER_PASSWORD,
    )
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
