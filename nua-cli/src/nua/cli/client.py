import os

from fabric import Connection


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

    def run(self, cmd: str, **kw):
        return self.connection.run(cmd, hide=True, **kw)
