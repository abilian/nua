from nua_cli.base import Command
from nua_cli.client import get_client

client = get_client()


class BackupCommand(Command):
    """Backup a deployed application."""

    name = "backup"

    def run(self):
        result = client.call_raw("backup")
        print(result)
