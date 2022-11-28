import nox

PYTHON_VERSIONS = ["3.10"]

nox.options.reuse_existing_virtualenvs = True
# nox.options.default_venv_backend = "venv"
nox.options.sessions = [
    "lint",
    "pytest",
    "doc",
]

SUB_REPOS = [
    "nua-lib",
    "nua-runtime",
    "nua-selfbuilder",
    "nua-build",
    "nua-orchestrator",
]


@nox.session(python=PYTHON_VERSIONS)
@nox.parametrize("sub_repo", SUB_REPOS)
def pytest(session: nox.Session, sub_repo: str):
    run_subsession(session, sub_repo)


@nox.session
@nox.parametrize("sub_repo", SUB_REPOS)
def lint(session: nox.Session, sub_repo: str):
    run_subsession(session, sub_repo)


@nox.session
def doc(session: nox.Session):
    print("TODO: do something with the docs")


@nox.session(name="update-deps")
def update_deps(session: nox.Session):
    for sub_repo in SUB_REPOS:
        with session.chdir(sub_repo):
            session.run("poetry", "install", external=True)
            session.run("poetry", "update", external=True)
        print()


def run_subsession(session, sub_repo):
    name = session.name.split("(")[0]
    print(f"\nRunning session: {session.name} in subrepo: {sub_repo}\n")
    with session.chdir(sub_repo):
        session.run("nox", "-e", name, external=True)
    print()
