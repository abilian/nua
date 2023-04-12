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

from nua_cli.base import CLI

snoop.install()


cli = CLI()
cli.add_option(
    "-h", "--help", default=False, action="store_true", help="Show help and exit"
)
cli.add_option(
    "-V", "--version", default=False, action="store_true", help="Show version and exit"
)
cli.add_option(
    "-d", "--debug", default=False, action="store_true", help="Enable debug mode"
)
cli.add_option(
    "-v", "--verbose", default=False, action="store_true", help="Increase verbosity"
)
cli.scan("nua_cli.commands")


if __name__ == "__main__":
    cli.run()
