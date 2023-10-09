from cleez.colors import red
from cleez.command import Argument, Command

from ..client import get_client
from .common import ORCH_PATH

client = get_client()


class StartCommand(Command):
    """Start an application."""

    name = "start"

    arguments = [
        Argument("app_id", help="Application ID"),
        Argument("domain", help="Domain name"),
    ]

    def run(self, app_id: str, domain: str):
        result = client.ssh(f"{ORCH_PATH} start -d {domain}")
        print(result.stdout)


class StopCommand(Command):
    """Stop an application."""

    # TODO: add --all option

    name = "stop"

    arguments = [
        Argument("app_id", help="Application ID"),
        Argument("domain", help="Domain name"),
    ]

    def run(self, app_id: str, domain: str):
        result = client.ssh(f"{ORCH_PATH} stop -d {domain}")
        print(result.stdout)


class RestartCommand(Command):
    """Restart an application."""

    name = "restart"

    arguments = [
        Argument("app_id", help="Application ID"),
        Argument("domain", help="Domain name"),
    ]

    def run(self, app_id: str, domain: str):
        result = client.ssh(f"{ORCH_PATH} restart -d {domain}")
        print(result.stdout)


class DestroyCommand(Command):
    """Destroy an application."""

    name = "destroy"

    arguments = [
        Argument("app_id", help="Application ID"),
        Argument("domain", help="Domain name"),
    ]

    # TODO: add confirmation step

    def run(self, app_id: str, domain: str):
        result = client.ssh(f"{ORCH_PATH} remove -d {domain}")
        print(result.stdout)


class UpdateCommand(Command):
    """Update an application."""

    name = "update"

    def run(self):
        print(red("Not implemented yet"))
