import nox
from pprint import pprint
import os

BASE_PYTHON_VERSION = "3.10"
PYTHON_VERSIONS = ["3.10"]


nox.options.pythons = PYTHON_VERSIONS
nox.options.default_venv_backend = "venv"
# nox.options.sessions = [
#     "lint",
#     "pytest",
#     "doc",
# ]

SUB_REPOS = [
    "nua-lib",
    "nua-runtime",
    "nua-selfbuilder",
    "nua-build",
    "nua-orchestrator",
]

print("Env:")
pprint(dict(sorted(os.environ.items())))
print()


@nox.session(python=PYTHON_VERSIONS)
@nox.parametrize("sub_repo", SUB_REPOS)
def pytest(session: nox.Session, sub_repo: str):
    run_subsession(session, sub_repo)


@nox.session(python=BASE_PYTHON_VERSION)
@nox.parametrize("sub_repo", SUB_REPOS)
def lint(session: nox.Session, sub_repo: str):
    run_subsession(session, sub_repo)


@nox.session(python=BASE_PYTHON_VERSION)
def doc(session: nox.Session):
    print("TODO: do something with the docs")


def run_subsession(session, sub_repo):
    name = session.name.split("(")[0]
    print(f"\nRunning session: {session.name} in subrepo: {sub_repo}\n")
    with session.chdir(sub_repo):
        session.run(
            "nox",
            "-e",
            name,
            "--reuse-existing-virtualenvs",
            external=True,
        )
    print()
