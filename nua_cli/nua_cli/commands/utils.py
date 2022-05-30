import json
import yaml
from hashlib import pbkdf2_hmac, sha256

import re
from random import choice
from string import ascii_letters

RE_BASIC_MAIL = re.compile(r"\S+@\S+\.\S+")


def as_json(obj):
    return json.dumps(
        obj, ensure_ascii=False, sort_keys=True, indent=4, separators=(",", ": ")
    )


def as_yaml(obj):
    return yaml.dump(obj, indent=2, width=50, default_flow_style=False)


def name_callback(value: str) -> str:
    value = value.strip()
    if not value:
        raise typer.BadParameter("Empty value is not allowed.")
    return value


def email_callback(value: str) -> str:
    value = value.strip()
    if not value:
        raise typer.BadParameter("Empty value is not allowed.")
    if not RE_BASIC_MAIL.match(value):
        raise typer.BadParameter("A valid mail address is required.")
    return value


def passwd_callback(value: str) -> str:
    min_length = 8
    value = value.strip()
    if len(value) < min_length:
        raise typer.BadParameter("The length must be at least {min_length} characters.")
    return value


def random_salt() -> str:
    salt_length = 32
    return "".join(choice(ascii_letters) for i in range(salt_length))


def salt_passwd(passwd: str, salt: str) -> str:
    iterations = 500000
    dk = pbkdf2_hmac("sha256", passwd.encode("utf8"), salt.encode("utf8"), iterations)
    return dk.hex()
