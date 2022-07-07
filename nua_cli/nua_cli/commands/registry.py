import sys

import typer
from tinyrpc.protocols.jsonrpc import JSONRPCProtocol

from ..config import config
from ..ssh import remote_exec
from .proxy import exit_on_rpc_error, get_proxy

app = typer.Typer()


@exit_on_rpc_error
@app.command()
def list() -> None:
    """List images available on Nua registry."""
    if config.get("mode") == "ssh":
        proto = JSONRPCProtocol()
        request = proto.create_request(method="docker_list")
        json_rpc_cmd = request.serialize().decode("utf8", "replace")
        response = remote_exec(json_rpc_cmd)
        if "result" in response:
            print("\n".join(response["result"]))
        else:
            print(response["error"])
    else:
        proxy = get_proxy()
        response_list = proxy.docker_list()
        print("\n".join(response_list))


if __name__ == "__main":
    app()
