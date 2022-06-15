"""configuration of the nua_build instance.

'config' is an adict.Dict(), if a dict is needed, use config.to_dict()
"""
from pathlib import Path

import toml
from addict import Dict

# at startup, config is empty, it will be completed from Nua DB
config = Dict()
# config = Dict(toml.load(Path(__file__).parent.resolve() / "nua_build.toml"))
