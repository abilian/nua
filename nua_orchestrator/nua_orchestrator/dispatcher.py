import sys
import traceback

from tinyrpc.dispatch import RPCDispatcher

from .rpc_utils import (
    available_methods,
    list_public_rpc_methods,
    register_rpc_local_methods,
    register_rpc_plugins,
    registered_classes,
)
from .server_utils.mini_log import log, log_me

registered_instances = []


def _register_rpc_methods(dispatcher, klass, config):
    try:
        obj = klass(config)
        registered_instances.append(obj)
        log("loading class", klass.__name__, "with prefix'", klass.prefix, "'")
        dispatcher.register_instance(obj, obj.prefix)
    except Exception as e:
        log_me(f"Error while register class {klass.__name__}")
        log_me(e)
        tb_info = traceback.format_tb(sys.exc_info()[2], limit=2)
        data = tb_info[1].strip()
        log_me(data)


def register_methods(config):
    global rpc_dispatcher
    register_rpc_local_methods()
    register_rpc_plugins(config)  # .read("nua", "rpc", "plugin"))
    dispatcher = RPCDispatcher()
    nua_config = config.read("nua")
    for klass in registered_classes:
        _register_rpc_methods(dispatcher, klass, nua_config)
    list_public_rpc_methods(dispatcher)
    log("registered methods:")
    for name in available_methods():
        log("    ", name)
    return dispatcher
