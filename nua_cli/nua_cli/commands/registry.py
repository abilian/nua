import typer

from .proxy import exit_on_rpc_error, get_proxy

app = typer.Typer()


@exit_on_rpc_error
@app.command()
def list() -> None:
    """List images available on Nua local registry."""
    proxy = get_proxy()
    response_list = proxy.docker_list()
    print("\n".join(response_list))


if __name__ == "__main":
    app()
