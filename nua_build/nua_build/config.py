"""configuration of the nua_build instance.
"""
from pathlib import Path

import toml

config = toml.load(Path(__file__).parent / "config.toml")
