from operator import itemgetter
from pprint import pp

from cleez import BadArgumentError
from cleez.command import Argument, Command

from ..client import get_client

client = get_client()


class ServerCommand(Command):
    """Manage the Nua server."""

    name = "server"
    hide_from_help = True

    def run(self):
        self.cli.print_help()


class LogsCommand(Command):
    """Show server logs."""

    name = "server logs"

    arguments = [
        Argument("service", help="Service to show logs for"),
    ]

    def run(self, service: str):
        if not service:
            print("Service must be one of: nua, letsencrypt, nginx")

        match service:
            case "nua":
                print("Showing Nua logs [TODO]")
            case "letsencrypt":
                result = client.ssh("cat log/letsencrypt/letsencrypt.log")
                print(result.stdout)
            case "nginx":
                print("Showing Nginx logs [TODO]")
            case _:
                raise BadArgumentError(
                    "Service must be one of: nua, letsencrypt, nginx"
                )


class StatusCommand(Command):
    """Show Nua status."""

    name = "server status"

    def run(self):
        result = client.call("status")

        print(f"Nua version: {result['version']}")

        registries = result["registries"]
        print("Configured registries:")
        for reg in sorted(registries, key=itemgetter("priority")):
            msg = (
                f'  priority: {reg["priority"]:>2}   '
                f'format: {reg["format"]:<16}   '
                f'url: {reg["url"]}'
            )
            print(msg)


class SettingsCommand(Command):
    """Show server settings."""

    name = "server settings"

    def run(self):
        result = client.call("settings")
        pp(result)


class PsCommand(Command):
    """List all server processes."""

    name = "server ps"

    def run(self):
        result = client.ssh("ps -aux")
        print(result.stdout)


class UptimeCommand(Command):
    """Show server uptime."""

    name = "server uptime"

    def run(self):
        result = client.ssh("uptime")
        print(result.stdout)


class CleanupCommand(Command):
    """Cleanup server (remove inactive docker images and containers)."""

    name = "server cleanup"

    # TODO: ask for confirmation

    def run(self):
        result = client.ssh("docker system prune -af")
        result = client.ssh("docker volume prune -f")
        print(result.stdout)
