#!/usr/bin/env python

import psycopg2
from psycopg2 import sql

#
# user = "bob"
# dbname = "mybase"
# passwd = "azerty"
# #
# con = psycopg2.connect(dbname=dbname, user=user, host="127.0.0.1", password=passwd)
# con.autocommit = True
#
# cur = con.cursor()
#

# cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(dbname)))
# sudo su - postgres
# psql postgres postgres
# ALTER USER postgres PASSWORD 'the_pass';
# \q
# psql -h localhost postgres postgres


def prompt_username(con):
    cur = con.cursor()
    while True:
        username = input("Enter User Name : ")
        cur.execute(
            "SELECT COUNT(*) FROM pg_catalog.pg_roles WHERE rolname = %s", [username]
        )
        (n,) = cur.fetchone()
        if n == 0:
            return username
        print("User already exists.")


def main():
    """create user"""
    con = psycopg2.connect(
        user="postgres",
        host="127.0.0.1",
        port="5432",
        password="the_pass",
    )

    username = prompt_username(con)
    password = input(f"Enter Password for {username} : ")
    query = sql.SQL("CREATE ROLE {0} LOGIN PASSWORD {1}").format(
        sql.Identifier(username),
        sql.Literal(password),
    )
    cur = con.cursor()
    cur.execute(query.as_string(con))
    cur.execute("COMMIT")


if __name__ == "__main__":
    main()
