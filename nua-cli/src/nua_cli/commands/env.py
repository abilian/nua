from cleez.colors import bold, red
from cleez.command import Argument, Command

from ..client import get_client
from ..common import get_current_app_id

client = get_client()


class EnvCommand(Command):
    """Manage an app's env variables."""

    name = "env"
    hide_from_help = True

    def run(self):
        self.cli.print_help()


class EnvShowCommand(Command):
    """Show application env variables."""

    name = "env show"

    arguments = [
        Argument("app_id", nargs="?", help="Application ID"),
    ]

    def run(self, app_id: str = ""):
        if not app_id:
            app_id = get_current_app_id()
        app_info = client.get_app_info(app_id)

        print(bold("Environment variables from the configuration:"))
        for k, v in sorted(app_info["site_config"]["env"].items()):
            print(f"{k}={repr(v)}")

        container_id = app_info["site_config"]["container_id"]
        try:
            container_info = client.get_container_info(container_id)
        except ValueError:
            print(red("Container not found - app is probably not running"))
            return

        print()
        print(bold("Environment variables from container:"))
        container_env = container_info[0]["Config"]["Env"]
        for k in sorted(container_env):
            print(k)


class EnvSetCommand(Command):
    """Show application env variables."""

    name = "env set"

    def run(self, app_id: str = ""):
        print(red("Not implemented yet"))
