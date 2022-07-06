import sys

import typer

from ..client import remote_exec
from ..config import config
from .proxy import exit_on_rpc_error, get_proxy

app = typer.Typer()


@exit_on_rpc_error
@app.command()
def list() -> None:
    """List images available on Nua local registry."""
    if config.get("mode") == "ssh":
        nua_args = " ".join(sys.argv[1:])[:2048]
        print(remote_exec(nua_args))
    else:
        proxy = get_proxy()
        response_list = proxy.docker_list()
        print("\n".join(response_list))


if __name__ == "__main":
    app()
