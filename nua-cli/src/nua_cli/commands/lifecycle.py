from nua_cli.base import Command, Argument
from nua_cli.client import get_client
from nua_cli.colors import red

client = get_client()

# Hardcoded for now
ORCH_PATH = "/home/nua/env/bin/nua-orchestrator"


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
