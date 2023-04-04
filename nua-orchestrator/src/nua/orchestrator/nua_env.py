"""Managing `os.environ` for Nua variables.

Basically a wrapper for the NUA_ENV dict as a singleton, no class
needed.
"""
import os
from copy import deepcopy
from pathlib import Path

from dotenv import dotenv_values

from .version import __version__

# todo: find NUA_SERVERNAME somewhere
NUA_ENV = {"NUA_SERVERNAME": "exemple.com"}


def nua_home() -> str:
    if not NUA_ENV.get("NUA_HOME"):
        detect_nua_home()
    return NUA_ENV.get("NUA_HOME", "")


def nua_home_path() -> Path:
    return Path(nua_home())


def detect_nua_home():
    """Load NUA_ENV with the path of the 'nua' user $HOME.

    - will raise RuntimeError if the 'nua' user is not created
    """
    NUA_ENV["NUA_HOME"] = str(Path("~nua").expanduser())


def nginx_path() -> Path:
    return nua_home_path() / "nginx"


def venv_bin() -> str:
    # Hack (hardcoded path), FIXME
    venv = "/home/nua/env"
    # venv = os.environ.get("VIRTUAL_ENV")
    # if not venv:
    #     venv = get_value("NUA_VENV")
    return os.path.join(venv, "bin")


def certbot_exe() -> str:
    return os.path.join(venv_bin(), "certbot")


def as_dict() -> dict:
    return deepcopy(NUA_ENV)


def set_value(key: str, value: str):
    NUA_ENV[key] = value


def get_value(key: str) -> str:
    return NUA_ENV.get(key, "")


# initializations
set_value("NUA_VERSION", __version__)
if (Path.home() / "ENV").exists():
    NUA_ENV.update(dotenv_values(Path.home() / "ENV"))
