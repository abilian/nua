from typer.testing import CliRunner
from nua_cli.main import app
from .utils import force_start
import re
import json
import yaml
from time import time

RE_SPLIT = re.compile(r"[^\w-]+")


runner = CliRunner()


# FIXME: for now, tests modify data in the default DB in /tmp
def test_help():
    result = runner.invoke(app, "users --help")
    assert result.exit_code == 0
    for cmd in "add count delete list update".split():
        assert f"  {cmd}" in result.stdout.split("Commands:", maxsplit=1)[-1]


def test_add_help():
    result = runner.invoke(app, "users add --help")
    assert result.exit_code == 0
    end_txt = result.stdout.split("Options:", maxsplit=1)[-1]
    for cmd in "--name --mail --password --help".split():
        assert cmd in set(RE_SPLIT.split(end_txt))


def test_count_help():
    result = runner.invoke(app, "users count --help")
    assert result.exit_code == 0
    end_txt = result.stdout.split("Options:", maxsplit=1)[-1]
    for cmd in "--help".split():
        assert cmd in set(RE_SPLIT.split(end_txt))


def test_delete_help():
    result = runner.invoke(app, "users delete --help")
    assert result.exit_code == 0
    end_txt = result.stdout.split("Options:", maxsplit=1)[-1]
    for cmd in "-i --id -n --name -m --mail --all --force --help".split():
        assert cmd in set(RE_SPLIT.split(end_txt))


def test_list_help():
    result = runner.invoke(app, "users list --help")
    assert result.exit_code == 0
    end_txt = result.stdout.split("Options:", maxsplit=1)[-1]
    for cmd in "-i --id -n --name -m --mail --all --json --help".split():
        assert cmd in set(RE_SPLIT.split(end_txt))


def test_update_help():
    result = runner.invoke(app, "users update --help")
    assert result.exit_code == 0
    end_txt = result.stdout.split("Options:", maxsplit=1)[-1]
    for cmd in "-i --id --key --value --help".split():
        assert cmd in set(RE_SPLIT.split(end_txt))


def test_count():
    force_start(runner)
    cmd = "users count"
    result = runner.invoke(app, cmd)
    assert result.exit_code == 0
    assert result.stdout.strip().isdigit()


def test_add_one():
    force_start(runner)
    name = f"x{int(time())}"
    mail = f"{name}@a.com"
    passwd = "12345678"
    cmd = f"users add --name {name} --mail {mail} --password {passwd}"
    before = runner.invoke(app, "users count")
    result = runner.invoke(app, cmd)
    after = runner.invoke(app, "users count")
    assert result.exit_code == 0
    assert int(after.stdout.strip()) == int(before.stdout.strip()) + 1


def test_list_yaml():
    force_start(runner)
    cnt = int(runner.invoke(app, "users count").stdout.strip())
    cmd = "users list"
    result = runner.invoke(app, cmd)
    assert result.exit_code == 0
    user_list = yaml.safe_load(result.stdout.strip())
    assert len(user_list) == cnt


def test_list_json():
    force_start(runner)
    cnt = int(runner.invoke(app, "users count").stdout.strip())
    cmd = "users list --json"
    result = runner.invoke(app, cmd)
    assert result.exit_code == 0
    user_list = json.loads(result.stdout.strip())
    assert len(user_list) == cnt


def test_update():
    force_start(runner)
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
    force_start(runner)
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
