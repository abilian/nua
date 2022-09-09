import os

import psycopg2
from flask import Flask, render_template

DB_NAME = "flask_db"
DB_USER = "sammy"
DB_USER_PWD = "sammy_pwd"
DB_HOST = "host.docker.internal"


app = Flask(__name__)


def get_db_connection():
    conn = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_HOST,
    )
    return conn


@app.route("/")
def index():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM books;")
    books = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("index.html", books=books)


if __name__ == "__main__":
    app.run(host="0.0.0.0")
