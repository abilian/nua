import typer

from .proxy import exit_on_rpc_error, get_proxy

app = typer.Typer()

argument_destination = typer.Argument(
    ..., metavar="destination", help="Remote address (user@host)"
)
argument_image_id = typer.Argument(..., metavar="image_id", help="Remote image id")


@exit_on_rpc_error
@app.command()
def load(
    destination: str = argument_destination,
    image_id: str = argument_image_id,
) -> None:
    """Load a remote image into Nua repository."""
    proxy = get_proxy()
    proxy.docker_load(destination, image_id)


@exit_on_rpc_error
@app.command()
def install(
    destination: str = argument_destination,
    image_id: str = argument_image_id,
) -> bool:
    """Install image from local repository to remote destination."""
    proxy = get_proxy()
    proxy.docker_install(destination, image_id)


@exit_on_rpc_error
@app.command()
def run(
    destination: str = argument_destination,
    image_id: str = argument_image_id,
) -> bool:
    """Start installed image on remote destination."""
    proxy = get_proxy()
    proxy.docker_run(destination, image_id)


if __name__ == "__main":
    app()
