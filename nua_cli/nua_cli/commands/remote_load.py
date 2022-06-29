from typing import List, Optional

import typer

from .proxy import exit_on_rpc_error, get_proxy

app = typer.Typer()

argument_remote = typer.Argument(metavar="remote", help="Remote account (user@host)")
argument_nua_tag = typer.Argument(
    metavar="nua_tag", help="Nua tag to apply (nua-some-app)"
)
argument_image_id = typer.Argument(metavar="image_id", help="Remote image id")


@exit_on_rpc_error
@app.command()
def rload(
    remote: str = argument_remote,
    nua_tag: str = argument_nua_tag,
    image_id: str = argument_image_id,
) -> None:
    """Load a remote docker image."""
    proxy = get_proxy()
    result = proxy.rload(remote, nua_tag, image_id)


if __name__ == "__main":
    app()
