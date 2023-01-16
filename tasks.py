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
def install(c):
    """Install all sub-packages (and dependencies)"""
    run_in_subrepos(c, "pip install -e .")


@task
def lint(c):
    """Lint (static check) the whole project."""
    # c.run("ruff .")
    # c.run("pre-commit run --all-files")

    run_in_subrepos(c, "make lint")


@task
def format(c):  # noqa: A001
    """Format the whole project."""
    run_in_subrepos(c, "make format")


@task
def test(c):
    """Run tests (in each subrepo)."""
    run_in_subrepos(c, "make test")


@task
def test_with_coverage(c):
    """Run tests with coverage (and combine results)."""
    run_in_subrepos(c, "pytest --cov nua")
    c.run("coverage combine */.coverage")
    # c.run("codecov --file .coverage")


@task
def mypy(c):
    """Run mypy (in each subrepo)."""
    run_in_subrepos(c, "mypy src")


@task
def pyright(c):
    """Run pyright (in each subrepo)."""
    run_in_subrepos(c, "pyright src")


@task
def clean(c):
    """Clean the whole project."""
    run_in_subrepos(c, "make clean")


@task
def fix(c):
    """Run ruff fixes in all subrepos."""
    run_in_subrepos(c, "ruff --fix src tests")


@task
def update(c):
    """Update dependencies the whole project."""
    c.run("poetry update")
    run_in_subrepos(c, "poetry update && poetry install")


@task
def graph(c):
    """Generate dependency graph in all subprojects."""
    run_in_subrepos(c, "mkdir -p doc")
    for sub_repo in SUB_REPOS:
        output = "doc/dependency-graph.png"
        target = f"src/nua/{sub_repo[4:]}"
        cmd = f"pydeps --max-bacon 2 --cluster -o {output} -T png {target}"
        h1(f"Running '{cmd}' in subrepos: {sub_repo}")
        with c.cd(sub_repo):
            c.run(cmd)


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
