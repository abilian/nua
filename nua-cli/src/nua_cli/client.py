import json
import sys
from io import StringIO

from cleez.colors import red
from fabric import Connection as BaseConnection
from invoke.runners import Result

from nua_cli.commands.common import get_nua_host, get_nua_user

# Hardcoded for now
NUA_CMD = "./env/bin/nua-orchestrator"


class Connection(BaseConnection):
    def run(self, command, **kwargs) -> Result:
        result = super().run(command, **kwargs)
        assert result
        return result


class Client:
    connection: Connection

    def __init__(self, host: str = "", user: str = ""):
        self.host = host
        self.user = user
        self.connection = Connection(self.host, self.user)

    #
    # Low level API
    #
    def call_raw(self, method: str, **kw) -> str:
        args = StringIO(json.dumps(kw))
        cmd = f"{NUA_CMD} rpc --raw {method}"
        r = self.connection.run(cmd, hide=True, in_stream=args)
        if r:
            return r.stdout
        else:
            return ""

    def call(self, method: str, **kw):
        args = StringIO(json.dumps(kw))
        cmd = f"{NUA_CMD} rpc {method}"
        r = self.connection.run(cmd, hide=True, in_stream=args)
        try:
            return json.loads(r.stdout)
        except json.JSONDecodeError:
            print(red(f"Invalid response from server:\n{r.stdout}"))
            sys.exit(1)

    def ssh(self, command: str):
        return self.connection.run(command, hide=True)

    #
    # Higher level API
    #
    def get_app_info(self, app_id: str) -> dict:
        result = self.call("list")

        app_info = None
        for instance in result:
            if instance["app_id"] == app_id:
                app_info = instance
                return app_info

        raise ValueError(f"App {app_id} not found")

    def get_container_info(self, container_id: str) -> dict:
        try:
            result = self.ssh(f"docker inspect {container_id}").stdout
            return json.loads(result)
        except:  # noqa
            raise ValueError(f"Container {container_id} not found")


_CLIENT = None


def get_client(host: str = "", user: str = ""):
    global _CLIENT

    if not host:
        host = get_nua_host()
    if not user:
        user = get_nua_user()

    if not _CLIENT:
        _CLIENT = Client(host, user)
    return _CLIENT
