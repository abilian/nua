import json
import os
import sys
from io import StringIO

import typer
from fabric import Connection

# Hardcoded for now
NUA_CMD = "./env/bin/nua-orchestrator"


class Client:
    connection: Connection

    def __init__(self, host: str = "", user: str = ""):
        if not host:
            host = os.environ.get("NUA_HOST", "localhost")
        if not user:
            user = os.environ.get("NUA_USER", "nua")

        self.host = host
        self.user = user
        self.connection = Connection(self.host, self.user)

    def call_raw(self, method: str, **kw):
        args = StringIO(json.dumps(kw))
        cmd = f"{NUA_CMD} rpc --raw {method}"
        r = self.connection.run(cmd, hide=True, in_stream=args)
        return r.stdout

    def call(self, method: str, **kw):
        args = StringIO(json.dumps(kw))
        cmd = f"{NUA_CMD} rpc {method}"
        r = self.connection.run(cmd, hide=True, in_stream=args)
        try:
            return json.loads(r.stdout)
        except json.JSONDecodeError:
            typer.secho(
                f"Invalid response from server:\n{r.stdout}", fg=typer.colors.RED
            )
            sys.exit(1)


_CLIENT = None


def get_client(host: str = "", user: str = ""):
    global _CLIENT

    if not _CLIENT:
        _CLIENT = Client(host, user)
    return _CLIENT
