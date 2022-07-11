"""configuration of the nua_build instance.
"""
from pathlib import Path

import tomli

with open(Path(__file__).parent / "config.toml", mode="rb") as rfile:
    config = tomli.load(rfile)
