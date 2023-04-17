from pprint import pp

from cleez import Command, CommandError
from cleez.command import Argument

from ..client import get_client
from ..common import get_current_app_id

client = get_client()


class ConfigCommand(Command):
    """Show/edit application config."""

    name = "config"
    hide_from_help = True

    def run(self):
        self.cli.print_help()


class ShowCommand(Command):
    """Show application config."""

    name = "config show"

    arguments = [
        Argument("app_id", nargs="?", help="Id of the application."),
    ]

    def run(self, app_id: str):
        result = client.call("list")

        if not app_id:
            app_id = get_current_app_id()
        if not app_id:
            raise CommandError("No app_id specified")

        for instance in result:
            if instance["app_id"] == app_id:
                pp(instance)
                break
        else:
            raise CommandError(f"App {app_id} not found")
