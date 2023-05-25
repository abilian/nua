"""Script to init the local mariadb password and access (for Nua user).

(Later: replace by flask ui access).
"""
import typer
from nua.lib.console import print_green

from ..db_utils.mariadb_utils import set_random_mariadb_pwd

# option_pwd = typer.Option(..., prompt=True, confirmation_prompt=True, hide_input=True)

app = typer.Typer()


@app.command("nua-mariadb-init")
# def nua_mariadb_init(password: str = option_pwd):
def nua_mariadb_init():
    """Inititalization (with random password) of the local MariaDB."""
    done = set_random_mariadb_pwd()
    if done:
        print_green("Password successfully changed.")
        raise SystemExit(0)
    else:
        print_green("Something went wrong.")
        raise SystemExit(1)
