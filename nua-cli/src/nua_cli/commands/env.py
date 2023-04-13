from operator import itemgetter
from pprint import pp

from nua_cli.base import Argument, Command
from nua_cli.client import get_client
from nua_cli.colors import red
from nua_cli.common import get_current_app_id
from nua_cli.exceptions import BadArgument

client = get_client()


class EnvShowCommand(Command):
    """Show application env variables."""

    name = "env show"

    arguments = [
        Argument("app_id", nargs='?', help="Application ID"),
    ]

    def run(self, app_id: str = ""):
        if not app_id:
            app_id = get_current_app_id()
        app_info = client.get_app_info(app_id)
        for k, v in app_info["site_config"]["env"].items():
            print(f"{k}={repr(v)}")


class EnvSetCommand(Command):
    """Show application env variables."""

    name = "env set"

    def run(self, app_id: str = ""):
        print(red("Not implemented yet"))


class EnvCommand(Command):
    """Manage an app's env variables."""

    name = "env"

    def run(self):
        self.cli.print_help()
