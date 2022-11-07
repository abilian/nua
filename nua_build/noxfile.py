import time
from random import randint

import nox
from nox.sessions import Session

PYTHON_VERSIONS = ["3.10", "3.11"]
# PACKAGE = "abilian"
# DB_DRIVERS = ["postgres", "postgres+pg8000"]

nox.options.reuse_existing_virtualenvs = True
nox.options.sessions = ("pytest", "lint")


@nox.session(python="python3.10")
def lint(session):
    session.run("poetry", "install", "-q")
    session.run("make", "lint")


@nox.session(python=PYTHON_VERSIONS)
def pytest(session):
    session.run("poetry", "install", "-q", external=True)
    session.run("pip", "check")
    session.run("pytest", "-q")


