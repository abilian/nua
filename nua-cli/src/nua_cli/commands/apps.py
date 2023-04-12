from nua_cli.base import Command
from nua_cli.client import get_client
from nua_cli.colors import green, red, yellow

client = get_client()


class AppsCommand(Command):
    """List applications."""

    name = "apps"

    def run(self):
        result = client.call("list")
        for instance in result:
            app_id = instance["app_id"]
            domain = instance["site_config"]["domain"]
            container_id = instance["site_config"]["container_id"]

            try:
                container_info = client.get_container_info(container_id)
            except ValueError:
                print(red(f"{app_id} @ {domain} - container not found"))
                continue

            status = container_info[0]["State"]["Status"]

            match status:
                case "running":
                    color = green
                case "exited":
                    color = red
                case _:
                    color = yellow

            print(color(f"{app_id} @ {domain} ({status})"))
