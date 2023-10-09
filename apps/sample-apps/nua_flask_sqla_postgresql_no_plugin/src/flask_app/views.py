from flask import redirect, render_template, request, url_for
from sqlalchemy import select

from .extensions import db
from .model import Book


def register_views(app):
    @app.route("/")
    def index():
        stmt = select(Book)
        books = db.session.scalars(stmt)
        return render_template("index.html", books=books)

    @app.route("/create/", methods=("GET", "POST"))
    def create():
        if request.method == "POST":
            # No validation...
            title = request.form["title"]
            author = request.form["author"]
            pages_num = int(request.form["pages_num"] or 0)
            review = request.form["review"]

            if title:
                book = Book(
                    title=title, author=author, pages_num=pages_num, review=review
                )
                db.session.add(book)
                db.session.commit()

            return redirect(url_for("index"))

        return render_template("create.html")
