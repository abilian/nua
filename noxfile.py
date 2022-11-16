import time
from random import randint

import nox
from nox.sessions import Session

BASE_PYTHON_VERSION = "3.10"
# PYTHON_VERSIONS = ["3.10", "3.11"]
PYTHON_VERSIONS = ["3.10"]

nox.options.sessions = [
    "lint",
    "pytest",
    "doc",
]

SUB_REPOS = [
    "nua-lib",
    "nua-runtime",
    "nua-build",
    "nua-orchestrator",
]


@nox.session(python=BASE_PYTHON_VERSION, venv_backend="venv")
def lint(session):
    run_subsessions(session)


@nox.session(python=PYTHON_VERSIONS, venv_backend="venv")
def pytest(session):
    run_subsessions(session)


@nox.session(python=BASE_PYTHON_VERSION, venv_backend="venv")
def doc(session):
    print("TODO: do something with the docs")


def run_subsessions(session):
    for sub_repo in SUB_REPOS:
        print(f"\nRunning session: {session.name} in subrepo: {sub_repo}\n")
        with session.chdir(sub_repo):
            session.run("nox", "-e", session.name, external=True)
        print()
