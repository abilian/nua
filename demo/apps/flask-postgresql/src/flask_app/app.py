from flask import Flask, redirect, render_template, request, url_for
from psycopg2.sql import SQL

from .db import db_connection

app = Flask(__name__)


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


@app.cli.command("init-db")
def init_db():
    """Initialize database (create table if needed)."""
    from .init_db import main

    main()
