import tempfile

from cleez import Command
from cleez.colors import bold

from ..client import get_client
from .common import NUA_ENV, get_config, get_nua_host, sh, ssh

client = get_client()

# Hardcoded for now
EXCLUDES = [
    ".git",
    ".env",
    ".venv",
    ".cache",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".nox",
    ".tox",
    ".coverage",
    ".idea",
    "dist",
    "build",
    "data",
    "doc",
    "vite/node_modules/",
    "front-old",
    "tmp",
    "sandbox",
]


class BuildCommand(Command):
    """Build app but don't deploy it."""

    name = "build"

    def run(self):
        host = get_nua_host()
        config = get_config()
        app_id = config["metadata"]["id"]

        build_dir = tempfile.mkdtemp(prefix=f"nua-build-{app_id}-", dir="/tmp")  # noqa

        print(bold(f"Building app {app_id}..."))

        excludes_args = " ".join([f"--exclude={e}" for e in EXCLUDES])
        ssh(f"mkdir -p {build_dir}", host=host)
        sh(f"rsync -e ssh --delete-after -az {excludes_args} ./ nua@{host}:{build_dir}")

        ssh(f"{NUA_ENV}/bin/nua-build -vvv {build_dir}", host)

        print()


# @cli.command()
#
#     verbosity = 1 + verbose - quiet
#     verbosity_flags = verbosity * ["-v"]
#
#     if experimental:
#         typer.secho(
#             "Using experimental builder (from nua-dev).", fg=typer.colors.YELLOW
#         )
#         subprocess.run(["nua-dev", "build", path])
#     else:
#         subprocess.run(["nua-build"] + verbosity_flags + [path])
#
