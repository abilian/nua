from pathlib import Path
from typing import List, Optional

import typer

from ..config import config
from ..keys_utils import is_private_key, parse_pub_key_content
from ..ssh import ssh_request
from .proxy import exit_on_rpc_error, get_proxy
from .utils import (
    as_json,
    as_yaml,
    email_callback,
    name_callback,
    passwd_callback,
    random_salt,
    salt_passwd,
)

app = typer.Typer()

option_name = typer.Option("", "--name", prompt=True, callback=name_callback)
option_mail = typer.Option("", prompt=True, callback=email_callback)
option_password = typer.Option(
    "",
    prompt=True,
    confirmation_prompt=True,
    hide_input=True,
    callback=passwd_callback,
)
option_with_id = typer.Option(
    None, "--id", "-i", help="Request user with ID (multiple use allowed)."
)
option_with_name = typer.Option(
    None, "--name", "-n", help="Request user with name (multiple use allowed)."
)
option_with_mail = typer.Option(
    None, "--mail", "-m", help="Request user with mail (multiple use allowed)."
)
option_all = typer.Option(False, "--all", help="Request all users.")

option_format_json = typer.Option(False, "--json", help="Format output as json.")


option_update_with_id = typer.Option(
    0, "--id", "-i", prompt=True, help="Request user with ID."
)
option_update_key = typer.Option("", prompt=True, callback=name_callback)
option_update_value = typer.Option(
    "",
    prompt=True,
)
option_delete_with_id = typer.Option(
    None, "--id", "-i", help="Request user with ID (multiple use allowed)."
)
option_delete_with_name = typer.Option(
    None, "--name", "-n", help="Request user with name (multiple use allowed)."
)
option_delete_with_mail = typer.Option(
    None, "--mail", "-m", help="Request user with mail (multiple use allowed)."
)
option_delete_all = typer.Option(False, "--all", help="Request all users.")
option_delete_force = typer.Option(False, "--force", help="No confirmation.")


@exit_on_rpc_error
@app.command()
def count() -> None:
    """Number or users in the table."""
    if config.get("mode") == "ssh":
        result = ssh_request("user_count")
    else:
        proxy = get_proxy()
        result = proxy.user_count()
    typer.echo(result)


@app.command()
@exit_on_rpc_error
def add(
    name: str = option_name,
    mail: str = option_mail,
    password: str = option_password,
) -> None:
    """Add user account."""
    salt = random_salt()
    salted_passwd = salt_passwd(password, salt)
    user_data = {
        "username": name,
        "email": mail,
        "password": salted_passwd,
        "salt": salt,
    }
    if config.get("mode") == "ssh":
        result = ssh_request("user_add", user_data)
    else:
        proxy = get_proxy()
        result = proxy.user_add(user_data)
    typer.echo(as_yaml(result))


@exit_on_rpc_error
@app.command()
def list(
    with_id: Optional[List[int]] = option_with_id,
    with_name: Optional[List[str]] = option_with_name,
    with_mail: Optional[List[str]] = option_with_mail,
    all: bool = option_all,
    format_json: bool = option_format_json,
) -> None:
    """List users accounts.

    Request by id, name and mail.
    """
    list_options = {
        "all": all,
        "ids": with_id,
        "names": with_name,
        "mails": with_mail,
    }
    if config.get("mode") == "ssh":
        lst = ssh_request("user_list", list_options)
    else:
        proxy = get_proxy()
        lst = proxy.user_list(list_options)
    if format_json:
        typer.echo(as_json(lst))
    else:
        typer.echo(as_yaml(lst))


@exit_on_rpc_error
@app.command()
def update(
    with_id: int = option_update_with_id,
    key: str = option_update_key,
    value: str = option_update_value,
) -> None:
    """Update some user account for one key/value pair.

    (value is of type 'str')
    """
    if not (with_id and key):
        typer.echo("No user selected.")
        return
    update_data = {
        "uid": with_id,
        "key": key,
        "value": value,
    }
    if config.get("mode") == "ssh":
        ssh_request("user_update", update_data)
    else:
        proxy = get_proxy()
        proxy.user_update(update_data)


def _validated_key_content(key_file: str) -> str:
    path = Path(key_file).expanduser()
    if not path.exists():
        typer.echo("File not found.")
        return ""
    with open(path, encoding="utf8") as rfile:
        key_content = rfile.read()
    # security check
    if is_private_key(key_content):
        typer.echo("Key not uploaded to server (key looks like a private key)")
        return ""
    if parse_pub_key_content(key_content) is None:
        typer.echo("Key not uploaded to server (key has unknown format)")
        return ""
    return key_content


@exit_on_rpc_error
@app.command()
def pubkey(
    username: str,
    key_name: str,
    key_file_or_erase: str,
) -> None:
    """Update some user account public key."""
    if not (username or not key_name):
        typer.echo("No user selected.")
        return
    if key_file_or_erase.strip().lower() == "erase":
        key_content = "erase"
    else:
        key_content = _validated_key_content(key_file_or_erase)
    if not key_content:
        return
    key_data = {"username": username, "key_name": key_name, "key_content": key_content}
    if config.get("mode") == "ssh":
        ssh_request("user_pubkey", key_data)
    else:
        proxy = get_proxy()
        proxy.user_pubkey(key_data)


def _ask_confirmation(user_list: list) -> bool:
    typer.secho("Users selected for deletion:", bold=True)
    for user in user_list:
        typer.echo(
            f'  - id: {user["id"]}, name:{user["username"]}, mail: {user["email"]}'
        )
    confirm = typer.confirm("Confirm deletion ?")
    return confirm


def _delete_all_users(force: bool) -> None:
    if force:
        confirm = True
    else:
        confirm = typer.confirm("Confirm deletion of all users ?")
    if confirm:
        proxy = get_proxy()
        proxy.user_delete_all()


def _delete_user_list(force: bool, request: dict) -> None:
    proxy = get_proxy()
    user_list = proxy.user_list(request)
    if not user_list:
        if not force:
            typer.echo("No user selected.")
        return
    if force:
        confirm = True
    else:
        confirm = _ask_confirmation(user_list)
    if confirm:
        ids = [u["id"] for u in user_list]
        proxy.user_delete(ids)


@exit_on_rpc_error
@app.command()
def delete(
    with_id: Optional[List[int]] = option_delete_with_id,
    with_name: Optional[List[str]] = option_delete_with_name,
    with_mail: Optional[List[str]] = option_delete_with_mail,
    all: bool = option_delete_all,
    force: bool = option_delete_force,
) -> None:
    """Delete users accounts.

    Request by id, name and mail.
    """
    if all or not (with_id or with_name or with_mail):
        _delete_all_users(force)
    else:
        request = {
            "all": all,
            "ids": with_id,
            "names": with_name,
            "mails": with_mail,
        }
        _delete_user_list(force, request)


if __name__ == "__main":
    app()
