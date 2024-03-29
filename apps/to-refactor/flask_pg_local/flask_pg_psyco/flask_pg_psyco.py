import psycopg2
from flask import Flask, redirect, render_template, request, url_for
from psycopg2.sql import SQL

from .constants import DB_HOST, DB_NAME, DB_USER, DB_USER_PWD

app = Flask(__name__)


def db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_USER_PWD,
    )


@app.route("/")
def index():
    connection = db_connection()
    cur = connection.cursor()
    cur.execute("SELECT * FROM books")
    books = cur.fetchall()
    cur.close()
    connection.close()
    return render_template("index.html", books=books)


@app.route("/create/", methods=("GET", "POST"))
def create():
    if request.method == "POST":
        title = request.form["title"]
        if title:
            author = request.form["author"]
            pages_num = int(request.form["pages_num"] or 0)
            review = request.form["review"]
            connection = db_connection()
            cur = connection.cursor()
            cur.execute(
                SQL(
                    "INSERT INTO books (title, author, pages_num, review)"
                    "VALUES (%s, %s, %s, %s)"
                ),
                (title, author, pages_num, review),
            )
            connection.commit()
            cur.close()
            connection.close()
        return redirect(url_for("index"))
    return render_template("create.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0")
