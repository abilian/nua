from nua_cli.base import Command


class MainCommand(Command):
    """Nua CLI."""

    name = ""

    def run(self):
        """Nua CLI."""

        self.cli.print_help()
