"""Example adapted from:

https://www.digitalocean.com/community/tutorials/how-to-use-a-postgresql-database-in-a-flask-application
"""
#
# RUN echo "listen_addresses='*'" >> /etc/postgresql/9.3/main/postgresql.conf
# RUN echo "host all  all    0.0.0.0/0  trust" >> /etc/postgresql/9.3/main/pg_hba.conf

import psycopg2

from nua.agent.db.postgres_manager import PostgresManager

from .constants import DB_HOST, DB_PORT, USER_DB, USER_NAME, USER_PASSWORD


def init_db():
    wait_for_db()
    load_content()


def wait_for_db():
    manager = PostgresManager(
        host=DB_HOST,
        port=DB_PORT,
        user=USER_NAME,
        password=USER_PASSWORD,
    )
    manager.wait_for_db()


def load_content():
    manager = PostgresManager(
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
    connection = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=USER_DB,
        user=USER_NAME,
        password=USER_PASSWORD,
    )
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
