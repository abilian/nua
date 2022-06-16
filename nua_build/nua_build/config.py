"""configuration of the nua_build instance.

'config' is an adict.Dict(), if a dict is needed, use config.to_dict()
"""
from addict import Dict

# at startup, config is empty, it will be completed from Nua DB
config = Dict()
