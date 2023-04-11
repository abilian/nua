"""
TODO:

[x] = done
[ ] = not done

[x] apps              List apps
[x] build             Build app but don't deploy it
[x] backup            Backup/restore app data
[x] config            Show/manage config for current app
[ ] deploy            Deploy app
[ ] destroy           Destroy app
[ ] help              Display help
[ ] init              Create a new app
[x] logs              Tail running logs
[ ] restart           Restart an app
[ ] run               Run a command in the app's environment
[ ] scale             Scale processes
[ ] server            Manage the Nua server
[ ] start             Start an app
[ ] status            Show app status
[ ] stop              Stop an app
[ ] update            Update an app
[x] version           Show Nua version
"""
from __future__ import annotations

import snoop

from .base import CLI

snoop.install()


cli = CLI()
cli.scan("nua_cli.commands")


# cli = typer.Typer()
# client = get_client()
#
#
# # Subcommands
# cli.add_typer(server.cli)
# cli.add_typer(config.cli)
#
#
# #
# # TODO: application lifecycle operations
# #

#
# @cli.callback(invoke_without_command=True)
# def main(
#     ctx: typer.Context,
#     version: Optional[bool] = OPTS["version"],
# ):
#     """Nua CLI."""
#     if ctx.invoked_subcommand is None:
#         print(ctx.get_help())
