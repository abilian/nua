from nua_cli.client import get_client
from nua_cli.colors import green, red, yellow

client = get_client()


class AppsCommand:
    """Manage applications."""

    name = "apps"

    def run(self):
        """List applications."""

        result = client.call("list")
        for instance in result:
            app_id = instance["app_id"]
            container_id = instance["site_config"]["container_id"]
            container_info = client.get_container_info(container_id)
            status = container_info[0]["State"]["Status"]

            match status:
                case "running":
                    color = green
                case "exited":
                    color = red
                case _:
                    color = yellow

            print(color(f"{app_id} ({status})"))
