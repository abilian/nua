from cleez.command import Argument, Command

from nua_cli.client import get_client
from nua_cli.common import get_current_app_id

client = get_client()


class LogsCommand(Command):
    """Show application logs."""

    name = "logs"

    arguments = [
        Argument("app_id", nargs="?", help="Application ID"),
    ]

    def run(self, app_id: str = ""):
        # Quick & dirty implementation that calls docker directly.
        if not app_id:
            app_id = get_current_app_id()
        app_info = client.get_app_info(app_id)
        container_id = app_info["site_config"]["container_id"]
        result = client.ssh(f"docker logs {container_id}")
        # Note: 'docker logs' returns data to both stderr and stdout.
        # We need to merge the two streams, on find another way
        print(result.stderr)
