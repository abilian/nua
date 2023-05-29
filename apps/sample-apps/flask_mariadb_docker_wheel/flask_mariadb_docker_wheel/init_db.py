"""Example adapted from:

https://www.digitalocean.com/community/tutorials/
    how-to-use-a-postgresql-database-in-a-flask-application
"""
#
# RUN echo "listen_addresses='*'" >> /etc/postgresql/9.3/main/postgresql.conf
# RUN echo "host all  all    0.0.0.0/0  trust" >> /etc/postgresql/9.3/main/pg_hba.conf

from datetime import datetime, timezone
from time import sleep, time

import mariadb

from .constants import DB_HOST, DB_PORT, USER_DB, USER_NAME, USER_PASSWORD


def main():
    wait_for_db()
    if not db_table_exist("books"):
        add_content()


def wait_for_db(timeout: int = 120):
    """Wait for the DB being up."""
    when = time()
    limit = when + timeout
    while time() < limit:
        while time() < when:
            sleep(0.1)
        try:
            mariadb.connect(
                host=DB_HOST,
                port=int(DB_PORT),
                database=USER_DB,
                user=USER_NAME,
                password=USER_PASSWORD,
            )
            now = datetime.now(timezone.utc).isoformat(" ")
            print(f"{now} - Connection ok")
            return
        except mariadb.Error:
            now = datetime.now(timezone.utc).isoformat(" ")
            print(f"{now} - Connection failed")
            when += 1.0
    raise RuntimeError(f"DB not available after {timeout} seconds.")


def db_table_exist(table: str) -> bool:
    connection = mariadb.connect(
        host=DB_HOST,
        port=int(DB_PORT),
        database=USER_DB,
        user=USER_NAME,
        password=USER_PASSWORD,
    )
    cursor = connection.cursor()
    query = (
        "SELECT count(*) FROM information_schema.TABLES WHERE "  # noqa S608
        f"(TABLE_SCHEMA = '{USER_DB}') AND (TABLE_NAME = '{table}')"
    )
    # cursor.execute(query, (dbname, table))
    cursor.execute(query)
    result = cursor.fetchone()
    count = result[0] if result else 0
    connection.close()
    return count > 0


def add_content():
    connection = mariadb.connect(
        host=DB_HOST,
        port=int(DB_PORT),
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
