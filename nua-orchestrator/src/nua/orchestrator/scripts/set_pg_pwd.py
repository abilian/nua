"""Script to set the local postgres password (for Nua user).

(Later: replace by flask ui access).
"""
import typer
from nua.lib.console import print_green, print_red

from ..db_utils.postgres_utils import set_postgres_pwd

option_pwd = typer.Option(..., prompt=True, confirmation_prompt=True, hide_input=True)

app = typer.Typer()


@app.command("set_pg_pwd")
def set_pg_pwd_app(password: str = option_pwd):
    """Set the Postgres password."""
    if len(password) < 8:
        print_red("New password is too short (at leat 8 chars).")
        raise SystemExit(1)
    done = set_postgres_pwd(password)
    if done:
        print_green("Password successfully changed.")
        raise SystemExit(0)
    else:
        print_green("Something went wrong.")
        raise SystemExit(1)
