import typer

from ..config import config
from ..ssh import ssh_request
from .proxy import exit_on_rpc_error, get_proxy

app = typer.Typer()


@app.command()
@exit_on_rpc_error
def add(
    username: str,
    host_label: str,
    host_account: str,
    host_address: str,
    host_port: int = 22,
) -> None:
    """Add host to list of managed hosts."""
    host_data = {
        "username": username,
        "host_label": host_label,
        "host_account": host_account,
        "host_address": host_address,
        "host_port": host_port,
    }
    if config.get("mode") == "ssh":
        result = ssh_request("user_host_add", host_data)
    else:
        proxy = get_proxy()
        result = proxy.user_host_add(host_data)
    if "message" in result:
        typer.echo(result["message"])
    else:
        typer.echo(result)


if __name__ == "__main":
    app()
