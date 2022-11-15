import time
from random import randint

import nox
from nox.sessions import Session

BASE_PYTHON_VERSION = "3.10"
PYTHON_VERSIONS = ["3.10", "3.11"]

nox.options.reuse_existing_virtualenvs = True
nox.options.sessions = [
    "pytest",
    "lint",
    "doc",
]

SUB_REPOS = [
    "nua-lib",
    "nua-build",
    "nua-orchestrator",
]


@nox.session(python=PYTHON_VERSIONS)
def pytest(session):
    run_subsessions(session)


@nox.session(python=BASE_PYTHON_VERSION)
def lint(session):
    run_subsessions(session)


@nox.session(python=BASE_PYTHON_VERSION)
def doc(session):
    print("TODO: do something with the docs")


def run_subsessions(session):
    for sub_repo in SUB_REPOS:
        print(f"\nRunning session: {session.name} in subrepo: {sub_repo}\n")
        with session.chdir(sub_repo):
            session.run("nox", "-e", session.name, external=True)
        print()
