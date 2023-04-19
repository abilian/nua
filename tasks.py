import os
import sys
from pathlib import Path

import tomlkit
from dotenv import load_dotenv
from invoke import Context, UnexpectedExit, task

load_dotenv()

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
RED = "\033[31m"


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
    project_info = tomlkit.load(Path("pyproject.toml").open())
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
# Release task
#


@task
def release(c: Context):
    """Release a new version."""
    c.run("make clean")

    pyproject_json = tomlkit.load(Path("pyproject.toml").open())
    version = pyproject_json["tool"]["poetry"]["version"]

    try:
        c.run("git diff --quiet")
    except UnexpectedExit:
        print("Your repo is dirty. Please commit or stash changes first.")
        sys.exit(1)

    h1("Checking versions are all set properly...")
    for sub_repo in SUB_REPOS:
        check_version_subrepo(c, sub_repo, version)

    c.run("git checkout release")
    c.run("git merge main")

    for sub_repo in SUB_REPOS:
        release_subrepo(c, sub_repo, version)

    c.run(f"git commit -a -m 'Release {version}'")
    c.run(f"git tag -a v{version} -m 'Release {version}'")
    c.run("git push origin release")
    c.run("git push --tags")
    c.run("git checkout main")


def check_version_subrepo(c, sub_repo, version):
    with c.cd(sub_repo):
        pyproject_json = tomlkit.load(Path("pyproject.toml").open())
        sub_version = pyproject_json["tool"]["poetry"]["version"]

        if sub_version != version:
            print(
                f"{RED}ERROR: version mismatch for {sub_repo}: "
                f"expected {version}, got {sub_version}{RESET}"
            )
            sys.exit(1)


def release_subrepo(c, sub_repo, version):
    h1(f"Releasing {sub_repo}...")

    old_pyproject = (Path(sub_repo) / "pyproject.toml").read_text()
    pyproject_json = tomlkit.loads(old_pyproject)

    if pyproject_json["tool"]["poetry"]["name"] == "nua-cli":
        pyproject_json["tool"]["poetry"]["name"] = "nua"

    deps = pyproject_json["tool"]["poetry"]["dependencies"]
    new_deps = {}
    for dep in deps:
        if dep.startswith("nua-"):
            new_deps[dep] = f"={version}"
        else:
            new_deps[dep] = deps[dep]

    pyproject_json["tool"]["poetry"]["dependencies"] = new_deps
    (Path(sub_repo) / "pyproject.toml").write_text(tomlkit.dumps(pyproject_json))

    with c.cd(sub_repo):
        c.run("poetry build")
        c.run("twine upload dist/*")


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
