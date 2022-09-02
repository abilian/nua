import json
import re
from time import time

import yaml
from typer.testing import CliRunner

from nua_cli.main import app

from .utils import force_start

RE_SPLIT = re.compile(r"[^\w-]+")


# FIXME: for now, tests modify data in the default DB in /tmp
def test_help():
    runner = CliRunner()

    result = runner.invoke(app, "users --help")

    assert result.exit_code == 0
    for cmd in ["add", "count", "delete", "list", "update"]:
        assert f"  {cmd}" in result.stdout.split("Commands:", maxsplit=1)[-1]


def test_add_help():
    runner = CliRunner()

    result = runner.invoke(app, "users add --help")

    assert result.exit_code == 0
    end_txt = result.stdout.split("Options:", maxsplit=1)[-1]
    for cmd in ["--name", "--mail", "--password", "--help"]:
        assert cmd in set(RE_SPLIT.split(end_txt))


def test_count_help():
    runner = CliRunner()

    result = runner.invoke(app, "users count --help")

    assert result.exit_code == 0
    end_txt = result.stdout.split("Options:", maxsplit=1)[-1]
    for cmd in ["--help"]:
        assert cmd in set(RE_SPLIT.split(end_txt))


def test_delete_help():
    runner = CliRunner()

    result = runner.invoke(app, "users delete --help")

    assert result.exit_code == 0
    end_txt = result.stdout.split("Options:", maxsplit=1)[-1]
    for cmd in [
        "-i",
        "--id",
        "-n",
        "--name",
        "-m",
        "--mail",
        "--all",
        "--force",
        "--help",
    ]:
        assert cmd in set(RE_SPLIT.split(end_txt))


def test_list_help():
    runner = CliRunner()

    result = runner.invoke(app, "users list --help")

    assert result.exit_code == 0
    end_txt = result.stdout.split("Options:", maxsplit=1)[-1]
    for cmd in [
        "-i",
        "--id",
        "-n",
        "--name",
        "-m",
        "--mail",
        "--all",
        "--help",
    ]:
        assert cmd in set(RE_SPLIT.split(end_txt))


def test_update_help():
    runner = CliRunner()

    result = runner.invoke(app, "users update --help")

    assert result.exit_code == 0
    end_txt = result.stdout.split("Options:", maxsplit=1)[-1]
    for cmd in ["-i", "--id", "--key", "--value", "--help"]:
        assert cmd in set(RE_SPLIT.split(end_txt))


def test_count():
    force_start()
    runner = CliRunner()
    cmd = "users count"

    result = runner.invoke(app, cmd)

    assert result.exit_code == 0
    assert result.stdout.strip().isdigit()


def test_add_one_1():
    force_start()
    name = f"x{int(time())}"
    mail = f"{name}@a.com"
    passwd = "12345678"  # noqa: S105
    cmd = f"users add --name {name} --mail {mail} --password {passwd}"
    runner = CliRunner()

    result = runner.invoke(app, cmd)

    assert result.exit_code == 0


def test_add_one_2():
    force_start()
    name = f"xy{int(time())}"
    mail = f"{name}@a.com"
    passwd = "12345678"  # noqa: S105
    cmd = f"users add --name {name} --mail {mail} --password {passwd}"
    runner = CliRunner()

    before = runner.invoke(app, "users count")
    runner.invoke(app, cmd)
    after = runner.invoke(app, "users count")

    result = int(after.stdout.strip()) - int(before.stdout.strip())
    assert result == 1


def test_list_yaml():
    force_start()
    runner = CliRunner()

    cnt = int(runner.invoke(app, "users count").stdout.strip())
    cmd = "users list"
    result = runner.invoke(app, cmd)

    assert result.exit_code == 0
    user_list = yaml.safe_load(result.stdout.strip())
    assert len(user_list) == cnt


def test_list_json():
    force_start()
    runner = CliRunner()

    cnt = int(runner.invoke(app, "users count").stdout.strip())
    cmd = "users list --json"
    result = runner.invoke(app, cmd)

    assert result.exit_code == 0
    user_list = json.loads(result.stdout.strip())
    assert len(user_list) == cnt


def test_update():
    force_start()
    runner = CliRunner()

    list_as_json = runner.invoke(app, "users list --json").stdout.strip()
    user_list = json.loads(list_as_json)
    uid = user_list[-1]["id"]
    new_mail = f"new_mail_{int(time())}@exemple.com"
    cmd = f"users update -i {uid} --key email --value {new_mail}"

    result = runner.invoke(app, cmd)

    assert result.exit_code == 0
    list_as_json = runner.invoke(app, "users list --json").stdout.strip()
    user_list = json.loads(list_as_json)
    users = [u for u in user_list if u["id"] == uid]
    user = users[0]
    assert user["email"] == new_mail


def test_delete():
    force_start()
    runner = CliRunner()

    list_as_json = runner.invoke(app, "users list --json").stdout.strip()
    user_list = json.loads(list_as_json)
    initial_count = len(user_list)
    uid = user_list[-1]["id"]
    cmd = f"users delete -i {uid} --force"

    result = runner.invoke(app, cmd)

    assert result.exit_code == 0
    list_as_json = runner.invoke(app, "users list --json").stdout.strip()
    user_list = json.loads(list_as_json)
    assert len(user_list) == initial_count - 1
    users = [u for u in user_list if u["id"] == uid]
    assert len(users) == 0
