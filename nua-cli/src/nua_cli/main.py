"""
TODO:

[x] = done
[ ] = not done

[x] apps              List apps
[x] build             Build app but don't deploy it
[x] backup            Backup/restore app data
[x] config            Show/manage config for current app
[x] deploy            Deploy app
[x] destroy           Destroy app
[x] help              Display help
[ ] init              Create a new app
[x] logs              Tail running logs
[x] restart           Restart an app
[ ] run               Run a command in the app's environment
[ ] scale             Scale processes
[x] server            Manage the Nua server
[x] start             Start an app
[x] status            Show app status
[x] stop              Stop an app
[ ] update            Update an app
[x] version           Show Nua version
"""
from __future__ import annotations

import snoop
from cleez import CLI
from cleez.actions import VERSION

from nua_cli.version import get_version

snoop.install()


def main():
    cli = get_cli()
    cli.run()


def get_cli():
    cli = CLI("nua", version=get_version())
    cli.add_option(
        "-V",
        "--version",
        action=VERSION,
        version=cli.version,
        default=False,
        help="Show version and exit",
    )
    cli.add_option(
        "-d", "--debug", default=False, action="store_true", help="Enable debug mode"
    )
    cli.add_option(
        "-v", "--verbose", default=False, action="store_true", help="Increase verbosity"
    )
    cli.scan("nua_cli.commands")
    return cli


if __name__ == "__main__":
    main()
