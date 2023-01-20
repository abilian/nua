from pathlib import Path

import sqlalchemy
from flask import Flask, redirect, render_template, request, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func

from .constants import DB_FOLDER, DB_NAME

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{Path(DB_FOLDER)/DB_NAME}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


class Student(db.Model):
    idt = db.Column(db.Integer, primary_key=True)
    firstname = db.Column(db.String(100), nullable=False)
    lastname = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(80), unique=True, nullable=False)
    age = db.Column(db.Integer)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    bio = db.Column(db.Text)

    def __repr__(self):
        return f"<Student {self.idt} {self.firstname} {self.firstname} {self.age}>"


def setup_db():
    db.create_all()
    if not Student.query.count():
        populate_db()


def populate_db():
    john = Student(
        firstname="john",
        lastname="doe",
        email="jd@example.com",
        age=23,
        bio="Biology student",
    )
    sammy = Student(
        firstname="Sammy",
        lastname="Shark",
        email="sammyshark@example.com",
        age=20,
        bio="Marine biology student",
    )

    carl = Student(
        firstname="Carl",
        lastname="White",
        email="carlwhite@example.com",
        age=22,
        bio="Marine geology student",
    )
    try:
        db.session.add(john)
        db.session.add(sammy)
        db.session.add(carl)
        db.session.commit()
    except sqlalchemy.exc.IntegrityError:
        pass


@app.route("/")
def index():
    students = Student.query.all()
    db_uri = app.config["SQLALCHEMY_DATABASE_URI"]
    return render_template("index.html", students=students, db_uri=db_uri)


@app.route("/<int:student_id>/")
def student(student_id):
    student = Student.query.get_or_404(student_id)
    return render_template("student.html", student=student)


@app.route("/create/", methods=("GET", "POST"))
def create():
    if request.method == "POST":
        firstname = request.form["firstname"] or "<unknown>"
        lastname = request.form["lastname"] or ""
        email = request.form["email"] or ""
        try:
            age = int(request.form["age"] or 0)
        except ValueError:
            age = 0
        bio = request.form["bio"] or "No bio."
        if lastname:
            student = Student(
                firstname=firstname, lastname=lastname, email=email, age=age, bio=bio
            )
            try:
                db.session.add(student)
                db.session.commit()
            except sqlalchemy.exc.IntegrityError:
                pass
        return redirect(url_for("index"))
    return render_template("create.html")


@app.route("/<int:student_id>/edit/", methods=("GET", "POST"))
def edit(student_id):
    student = Student.query.get_or_404(student_id)
    if request.method == "POST":
        firstname = request.form["firstname"] or "<unknown>"
        lastname = request.form["lastname"] or ""
        email = request.form["email"] or ""
        try:
            age = int(request.form["age"])
        except ValueError:
            age = 0
        bio = request.form["bio"] or "No bio."
        student.firstname = firstname
        student.lastname = lastname
        student.email = email
        student.age = age
        student.bio = bio

        db.session.add(student)
        db.session.commit()
        # except sqlalchemy.exc.IntegrityError:
        # pass
        return redirect(url_for("index"))
    return render_template("edit.html", student=student)


@app.post("/<int:student_id>/delete/")
def delete(student_id):
    student = Student.query.get_or_404(student_id)
    db.session.delete(student)
    db.session.commit()
    return redirect(url_for("index"))


# setup_db()
