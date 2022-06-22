"""configuration of the nua_orchestrator server.

'config' is an DeepAccessDict(), if a dict is needed, use config.get()
"""
from .deep_access_dict import DeepAccessDict

# at startup, config is empty, it will be completed from Nua DB
config = DeepAccessDict()
