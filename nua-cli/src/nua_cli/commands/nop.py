from nua_cli.base import Command
from nua_cli.colors import red


class RestoreCommand(Command):
    """Restore backup data of a deployed application."""

    name = "restore"

    def run(self):
        print(red("Not implemented yet"))


class UpdateCommand(Command):
    """Update an application."""

    name = "update"

    def run(self):
        print(red("Not implemented yet"))


class DestroyCommand(Command):
    """Destroy an application."""

    name = "destroy"

    def run(self):
        print(red("Not implemented yet"))


class StartCommand(Command):
    """Start an application."""

    name = "start"

    def run(self):
        print(red("Not implemented yet"))


class StopCommand(Command):
    """Stop an application."""

    name = "stop"

    def run(self):
        print(red("Not implemented yet"))
