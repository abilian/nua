from typing import Optional, List
import typer

from .proxy import get_proxy, abort_rpc_error
from .utils import (
    as_json,
    as_yaml,
    name_callback,
    email_callback,
    passwd_callback,
    salt_passwd,
    random_salt,
)

app = typer.Typer()


@abort_rpc_error
@app.command()
def count() -> None:
    """
    Number or users in the table.
    """
    proxy = get_proxy()
    cnt = proxy.user_count()
    typer.echo(cnt)


@app.command()
@abort_rpc_error
def add(
    name: str = typer.Option("", "--name", prompt=True, callback=name_callback),
    mail: str = typer.Option("", prompt=True, callback=email_callback),
    password: str = typer.Option(
        "",
        prompt=True,
        confirmation_prompt=True,
        hide_input=True,
        callback=passwd_callback,
    ),
) -> None:
    """
    Add user account.
    """
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
    with_id: Optional[List[int]] = typer.Option(
        None, "--id", "-i", help="Request user with ID (multiple use allowed)."
    ),
    with_name: Optional[List[str]] = typer.Option(
        None, "--name", "-n", help="Request user with name (multiple use allowed)."
    ),
    with_mail: Optional[List[str]] = typer.Option(
        None, "--mail", "-m", help="Request user with mail (multiple use allowed)."
    ),
    all: bool = typer.Option(False, "--all", help="Request all users."),
    format_json: bool = typer.Option(False, "--json", help="Format output as json."),
) -> None:
    """
    List users accounts. Request by id, name and mail.
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
    with_id: int = typer.Option(
        0, "--id", "-i", prompt=True, help="Request user with ID."
    ),
    key: str = typer.Option("", prompt=True, callback=name_callback),
    value: str = typer.Option(
        "",
        prompt=True,
    ),
) -> None:
    """
    Update some user account for one key/value pair.
    (value is of type 'str')
    """
    if not (with_id and key):
        typer.echo("No user selected.")
        return
    proxy = get_proxy()
    proxy.user_update(with_id, key, value)


@abort_rpc_error
@app.command()
def delete(
    with_id: Optional[List[int]] = typer.Option(
        None, "--id", "-i", help="Request user with ID (multiple use allowed)."
    ),
    with_name: Optional[List[str]] = typer.Option(
        None, "--name", "-n", help="Request user with name (multiple use allowed)."
    ),
    with_mail: Optional[List[str]] = typer.Option(
        None, "--mail", "-m", help="Request user with mail (multiple use allowed)."
    ),
    all: bool = typer.Option(False, "--all", help="Request all users."),
    force: bool = typer.Option(False, "--force", help="No confirmation."),
) -> None:
    """
    Delete users accounts. Request by id, name and mail.
    """
    if all or not (with_id or with_name or with_mail):
        if force:
            confirm = True
        else:
            confirm = typer.confirm("Confirm deletion of all users ?")
        if confirm:
            proxy = get_proxy()
            proxy.user_delete_all()
        return
    request = {
        "all": all,
        "ids": with_id,
        "names": with_name,
        "mails": with_mail,
    }
    proxy = get_proxy()
    lst = proxy.user_list(request)
    if not lst:
        if not force:
            typer.echo("No user selected.")
        return
    if force:
        confirm = True
    else:
        typer.secho("Users selected for deletion:", bold=True)
        for user in lst:
            typer.echo(
                f'  - id: {user["id"]}, name:{user["username"]}, mail: {user["email"]}'
            )
        confirm = typer.confirm("Confirm deletion ?")
    if confirm:
        ids = [u["id"] for u in lst]
        proxy.user_delete(ids)


if __name__ == "__main":
    app()
