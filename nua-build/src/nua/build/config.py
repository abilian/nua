"""configuration of the nua_build instance."""
from importlib import resources as rso

import tomli

config = tomli.loads(rso.read_text("nua.build.default_conf", "config.toml"))
