"""configuration of the nua_build instance.

'config' is an DeepAccessDict(), if a dict is needed, use config.read()
"""
from .deep_access_dict import DeepAccessDict

# at startup, config is empty, it will be completed from Nua DB
config = DeepAccessDict()
