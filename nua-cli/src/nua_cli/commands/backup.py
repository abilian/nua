from cleez import Command
from cleez.colors import red

from ..client import get_client

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
