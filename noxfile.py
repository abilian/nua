# import time
# from random import randint

import nox
from nox.sessions import Session

BASE_PYTHON_VERSION = "3.10"
PYTHON_VERSIONS = ["3.10"]


nox.options.pythons = ["3.10"]
nox.options.default_venv_backend = "venv"
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


@nox.session(python=PYTHON_VERSIONS)
def lint(session: nox.Session):
    run_subsessions(session)


@nox.session(python=PYTHON_VERSIONS)
def pytest(session: nox.Session):
    run_subsessions(session)


@nox.session(python=PYTHON_VERSIONS)
def doc(session: nox.Session):
    print("TODO: do something with the docs")


def run_subsessions(session: nox.Session):
    for sub_repo in SUB_REPOS:
        print(f"\nRunning session: {session.name} in subrepo: {sub_repo}\n")
        with session.chdir(sub_repo):
            session.run(
                "nox",
                "-e",
                session.name,
                "--reuse-existing-virtualenvs",
                external=True,
            )
        print()
