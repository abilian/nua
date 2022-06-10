from typing import List, Optional

import typer

from .proxy import abort_rpc_error, get_proxy
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
option_all = (typer.Option(False, "--all", help="Request all users."),)
format_json: bool = typer.Option(False, "--json", help="Format output as json.")
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


@abort_rpc_error
@app.command()
def count() -> None:
    """Number or users in the table."""
    proxy = get_proxy()
    cnt = proxy.user_count()
    typer.echo(cnt)


@app.command()
@abort_rpc_error
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
    proxy = get_proxy()
    result = proxy.user_add(user_data)
    typer.echo(as_yaml(result))
    cnt = proxy.user_count()
    typer.echo(f"Number of users in table is now: {cnt}")


@abort_rpc_error
@app.command()
def list(
    with_id: Optional[List[int]] = option_with_id,
    with_name: Optional[List[str]] = option_with_name,
    with_mail: Optional[List[str]] = option_with_mail,
    all: bool = option_all,
) -> None:
    """List users accounts.

    Request by id, name and mail.
    """
    request = {
        "all": all,
        "ids": with_id,
        "names": with_name,
        "mails": with_mail,
    }
    proxy = get_proxy()
    lst = proxy.user_list(request)
    if format_json:
        typer.echo(as_json(lst))
    else:
        typer.echo(as_yaml(lst))


@abort_rpc_error
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
    proxy = get_proxy()
    proxy.user_update(with_id, key, value)


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


@abort_rpc_error
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
