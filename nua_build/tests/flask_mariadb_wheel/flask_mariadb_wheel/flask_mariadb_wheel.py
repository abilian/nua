import mariadb
from flask import Flask, redirect, render_template, request, url_for

from .constants import DB_HOST, DB_NAME, DB_USER, DB_USER_PWD

app = Flask(__name__)


def db_connection():
    return mariadb.connect(
        user=DB_USER,
        password=DB_USER_PWD,
        host=DB_HOST,  # Your server name
        port=3306,
        database=DB_NAME,
    )


@app.route("/")
def index():
    # data = []
    connection = db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM books")
    books = cursor.fetchall()
    cursor.close()
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
            cursor = connection.cursor()
            cursor.execute(
                "INSERT INTO books (title, author, pages_num, review)"
                "VALUES (?, ?, ?, ?)",
                (title, author, pages_num, review),
            )
            connection.commit()
            connection.close()
        return redirect(url_for("index"))
    return render_template("create.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0")
