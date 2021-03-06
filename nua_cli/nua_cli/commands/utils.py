import json
import re
import secrets
from hashlib import pbkdf2_hmac, sha256  # noqa: F401

import typer
import yaml

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
    # salt_length = 16bytes, len()=22 because base64 encoding
    return secrets.token_urlsafe(16)


def salt_passwd(passwd: str, salt: str) -> str:
    iterations = 500000
    dk = pbkdf2_hmac("sha256", passwd.encode("utf8"), salt.encode("utf8"), iterations)
    return dk.hex()
