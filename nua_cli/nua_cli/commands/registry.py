import sys

import typer
from tinyrpc.protocols.jsonrpc import JSONRPCProtocol

from ..config import config
from ..ssh import ssh_request
from .proxy import exit_on_rpc_error, get_proxy

app = typer.Typer()


@exit_on_rpc_error
@app.command()
def list() -> None:
    """List images available on Nua registry."""
    if config.get("mode") == "ssh":
        result = ssh_request("docker_list")
        if result:
            print("\n".join(result))
    else:
        proxy = get_proxy()
        response_list = proxy.docker_list()
        print("\n".join(response_list))


if __name__ == "__main":
    app()
