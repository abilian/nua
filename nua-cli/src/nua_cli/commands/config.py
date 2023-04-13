from pprint import pp

from nua_cli.base import Argument, Command
from nua_cli.client import get_client
from nua_cli.common import get_current_app_id
from nua_cli.exceptions import CommandError

client = get_client()


class ShowCommand(Command):
    """Show application config."""

    name = "config show"

    arguments = [
        Argument("app_id", nargs='?', help="Id of the application."),
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


class ConfigCommand(Command):
    """Show/edit application config."""

    name = "config"

    def run(self):
        self.cli.print_help()
