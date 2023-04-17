from cleez import Command

from nua_cli.client import get_client
from nua_cli.version import get_version

client = get_client()


class HelpCommand(Command):
    """Show help."""

    name = "help"

    def run(self):
        self.cli.print_help()


class VersionCommand:
    """Show Nua version."""

    name = "version"

    def run(self):
        print(f"Nua CLI version: {get_version()}")
        status = client.call("status")
        print(f"Nua Server version: {status['version']}")
