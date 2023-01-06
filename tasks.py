from invoke import task

SUB_REPOS = [
    "nua-lib",
    "nua-cli",
    "nua-runtime",
    "nua-autobuild",
    "nua-build",
    "nua-orchestrator",
]


@task
def lint(c):
    # c.run("ruff .")
    # c.run("pre-commit run --all-files")

    run_make_in_subrepos(c, "lint")


@task
def format(c):  # noqa: A001
    run_make_in_subrepos(c, "format")


#
# Helpers
#


def h1(msg):
    print()
    print(msg)
    print("=" * len(msg))
    print()


def run_make_in_subrepos(c, target):
    for sub_repo in SUB_REPOS:
        h1(f"Running {target} in subrepos: {sub_repo}")
        with c.cd(sub_repo):
            c.run(f"make {target}")
