"""Managing os.environ for Nua variables.

Basically a wrapper for the NUA_ENV dict as a singleton, no class
needed.
"""
from copy import deepcopy
from pathlib import Path

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
    return nua_home() / "nginx"


def as_dict() -> dict:
    return deepcopy(NUA_ENV)


def set(key: str, value: str):
    NUA_ENV[key] = value


def get(key: str) -> str:
    return NUA_ENV.get("NUA_HOME", "")
