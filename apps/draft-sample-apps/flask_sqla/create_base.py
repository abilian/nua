#!/usr/bin/env python

import psycopg2
from psycopg2 import sql


def create_db(dbname, user):
    """create db."""

    con = psycopg2.connect(
        dbname="postgres", user="postgres", host="127.0.0.1", password="the_pass"
    )
    con.autocommit = True

    cur = con.cursor()

    cur.execute(
        sql.SQL("CREATE DATABASE {} OWNER {};").format(
            sql.Identifier(dbname), sql.Identifier(user)
        )
    )


if __name__ == "__main__":
    create_db("mybase", "some_user")
    # sudo su - postgres -c 'psql -c "\l"'
