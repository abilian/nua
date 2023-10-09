"""Managing `os.environ` for Nua variables.

Basically a wrapper for the self._env dict as a singleton, no class
needed.
"""
import os
from copy import deepcopy
from pathlib import Path

from dotenv import dotenv_values

from .version import __version__

# todo: find NUA_SERVERNAME somewhere
NUA_ENV = {"NUA_SERVERNAME": "exemple.com"}


class NuaEnv:
    """Managing `os.environ` for Nua variables."""

    def __init__(self):
        self._env = deepcopy(NUA_ENV)

        # initializations
        self.set_value("NUA_VERSION", __version__)
        if (Path.home() / "ENV").exists():
            self._env.update(dotenv_values(Path.home() / "ENV"))

    def nua_home(self) -> str:
        if not self._env.get("NUA_HOME"):
            self.detect_nua_home()
        return self._env.get("NUA_HOME", "")

    def nua_home_path(self) -> Path:
        return Path(self.nua_home())

    def detect_nua_home(self):
        """Load self._env with the path of the 'nua' user $HOME.

        - will raise RuntimeError if the 'nua' user is not created
        """
        self._env["NUA_HOME"] = str(Path("~nua").expanduser())

    def nginx_path(self) -> Path:
        return self.nua_home_path() / "nginx"

    def venv_bin(self) -> str:
        # Hack (hardcoded path), FIXME
        venv = "/home/nua/env"
        # venv = os.environ.get("VIRTUAL_ENV")
        # if not venv:
        #     venv = get_value("NUA_VENV")
        return os.path.join(venv, "bin")

    def certbot_exe(self) -> str:
        return os.path.join(self.venv_bin(), "certbot")

    def as_dict(self) -> dict:
        return deepcopy(self._env)

    def set_value(self, key: str, value: str):
        self._env[key] = value

    def get_value(self, key: str) -> str:
        return self._env.get(key, "")


# Singleton
nua_env = NuaEnv()
