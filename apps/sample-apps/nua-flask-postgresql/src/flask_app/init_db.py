"""Example adapted from:

https://www.digitalocean.com/community/tutorials/how-to-use-a-postgresql-database-in-a-flask-application
"""
from psycopg2.sql import SQL

from .db import db_connection, wait_for_db

BOOKS = [
    ("A Tale of Two Cities", "Charles Dickens", 489, "A great classic!"),
    ("Anna Karenina", "Leo Tolstoy", 864, "Another great classic!"),
]


def main():
    wait_for_db()
    create_content()


def create_content():
    if not table_exist("books"):
        create_table()
        insert_content()


def table_exist(table: str) -> bool:
    """Check if the named database exists (for host, connecting as user),
    assuming DB exists."""
    connection = db_connection()
    with connection:  # noqa SIM117
        with connection.cursor() as cur:
            query = "SELECT COUNT(*) FROM information_schema.tables WHERE table_name=%s"
            cur.execute(SQL(query), (table,))
            result = cur.fetchone()
            count = result[0] if result else 0
    connection.close()
    return count > 0


def create_table():
    connection = db_connection()
    with connection:  # noqa SIM117
        with connection.cursor() as cur:
            # Execute a command: this creates a new table
            cur.execute("DROP TABLE IF EXISTS books;")
            cur.execute(
                "CREATE TABLE books (id serial PRIMARY KEY,"
                "title varchar (150) NOT NULL,"
                "author varchar (50) NOT NULL,"
                "pages_num integer NOT NULL,"
                "review text,"
                "date_added date DEFAULT CURRENT_TIMESTAMP);"
            )
            connection.commit()
    connection.close()


def insert_content():
    connection = db_connection()
    with connection:  # noqa SIM117
        with connection.cursor() as cur:
            # Insert data into the table

            sql_stmt = (
                "INSERT INTO books (title, author, pages_num, review)"
                "VALUES (%s, %s, %s, %s)"
            )
            for book in BOOKS:
                cur.execute(sql_stmt, book)

            connection.commit()
    connection.close()
