from nua_cli.base import Command
from nua_cli.client import get_client
from nua_cli.colors import red

client = get_client()


class BackupCommand(Command):
    """Backup a deployed application."""

    name = "backup"

    def run(self):
        result = client.call_raw("backup")
        print(result)


class RestoreCommand(Command):
    """Restore backup data of a deployed application."""

    name = "restore"

    def run(self):
        print(red("Not implemented yet"))
