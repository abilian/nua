import os
import sys
from pathlib import Path

try:
    import tomllib
except ImportError:
    import tomli as tomllib

from dotenv import load_dotenv
from invoke import task

load_dotenv()

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"


SUB_REPOS = [
    "nua-lib",
    "nua-cli",
    "nua-agent",
    "nua-autobuild",
    "nua-build",
    "nua-orchestrator",
]

RSYNC_EXCLUDES = [
    # ".git",
    ".env",
    ".venv",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "dist",
    "build",
    ".nox",
    ".tox",
    ".cache",
    ".coverage",
]

try:
    from abilian_devtools.invoke import import_tasks

    import_tasks(globals())
except ImportError:
    pass


#
# Subrepos tasks
#
@task
def install(c, quiet=False):
    """Install all sub-packages (and dependencies)"""
    # first uninstall all
    c.run(
        "pip list --format freeze |grep nua- |xargs pip uninstall -yq &>/dev/null",
        warn=True,
    )
    if quiet:
        run_in_subrepos(c, "pip install -qq --no-cache-dir -e .")
    else:
        run_in_subrepos(c, "pip install --no-cache-dir -e .")


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
def run(c, cmd: str):
    """Run given command in all subrepos."""
    run_in_subrepos(c, cmd)


@task
def update(c):
    """Update dependencies the whole project."""
    c.run("poetry update")
    run_in_subrepos(c, "poetry update && poetry install")


#
# Other tasks
#
@task
def bump_version(c, bump: str = "patch"):
    """Update version - use 'patch' (default), 'minor' or 'major' as an argument."""

    c.run(f"poetry version {bump}")
    project_info = tomllib.load(Path("pyproject.toml").open("rb"))
    version = project_info["tool"]["poetry"]["version"]
    run_in_subrepos(c, f"poetry version {version}")


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


@task
def watch(c, host=None):
    """Watch for changes and push to a remote server."""
    import watchfiles

    if not host:
        host = os.environ.get("NUA_HOST")
    if not host:
        print(
            "Please set NUA_HOST env var or "
            "pass it as an argument (--host=example.com)."
        )
        sys.exit()

    excludes_args = " ".join([f"--exclude={e}" for e in RSYNC_EXCLUDES])

    def sync():
        print(f"{BOLD}Syncing to remote server (nua@{host})...{DIM}")
        c.run(f"rsync -e ssh -avz {excludes_args} ./ nua@{host}:/home/nua/src/")

    sync()
    for _changes in watchfiles.watch("."):
        print("Changes detected, syncing...")
        sync()


#
# Helpers
#


def h1(msg):
    print()
    print(BOLD + msg + RESET)
    print()


def run_in_subrepos(c, cmd):
    for sub_repo in SUB_REPOS:
        h1(f"Running '{cmd}' in subrepos: {sub_repo}")
        with c.cd(sub_repo):
            c.run(cmd)
