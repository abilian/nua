from invoke import task

SUB_REPOS = [
    "nua-lib",
    "nua-cli",
    "nua-runtime",
    "nua-autobuild",
    "nua-build",
    "nua-orchestrator",
]


#
# Tasks
#


@task
def lint(c):
    # c.run("ruff .")
    # c.run("pre-commit run --all-files")

    run_in_subrepos(c, "make lint")


@task
def format(c):  # noqa: A001
    run_in_subrepos(c, "make format")


@task
def test(c):
    run_in_subrepos(c, "make test")


@task
def mypy(c):
    run_in_subrepos(c, "mypy src")


@task
def pyright(c):
    run_in_subrepos(c, "pyright src")


@task
def clean(c):
    run_in_subrepos(c, "clean")


@task
def update(c):
    run_in_subrepos(c, "poetry update && poetry install")


#
# Helpers
#


def h1(msg):
    print()
    print(msg)
    print("=" * len(msg))
    print()


def run_in_subrepos(c, cmd):
    for sub_repo in SUB_REPOS:
        h1(f"Running '{cmd}' in subrepos: {sub_repo}")
        with c.cd(sub_repo):
            c.run(cmd)
