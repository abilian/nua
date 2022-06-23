import sys
import traceback
from copy import deepcopy
from functools import wraps
from importlib import import_module
from pathlib import Path

from tinyrpc.protocols.jsonrpc import JSONRPCServerError

from .server_utils.mini_log import log_me

# list of classes containing rpc methods.
registered_classes = []
public_methods = []


def rpc_trace(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except Exception as e:
            tb_info = traceback.format_tb(sys.exc_info()[2], limit=2)
            raise JSONRPCServerError(e, data=tb_info[1].strip())

    return wrapper


def register_rpc_local_methods():
    folder = Path(__file__).parent / "methods"
    base = __name__.split(".")[:-1]
    base.append("methods")
    base_name = ".".join(base)
    for module_file in folder.glob("*.py"):
        if module_file.name.startswith("_"):
            continue
        mod_name = module_file.stem
        try:
            import_module(f"{base_name}.{mod_name}")
        except Exception as e:
            log_me(f"Error loading local {module_file}")
            log_me(e)
            tb_info = traceback.format_tb(sys.exc_info()[2], limit=2)
            data = tb_info[1].strip()
            log_me(data)


def register_rpc_plugins(plugin_list):
    if not plugin_list:
        return
    for plugin in plugin_list:
        try:
            tmp = import_module(plugin["module"])
            klass = getattr(tmp, plugin["class"])
            del tmp
            if klass not in registered_classes:
                registered_classes.append(klass)
        except Exception as e:
            log_me(f"Error loading plugin {plugin}")
            log_me(e)
            tb_info = traceback.format_tb(sys.exc_info()[2], limit=2)
            data = tb_info[1].strip()
            log_me(data)


def register_methods(klass):
    if klass not in registered_classes:
        registered_classes.append(klass)


def dispatcher_methods(dispatcher, prefix=""):
    lst = []
    lst.extend([f"{prefix}{name}" for name in dispatcher.method_map])
    for sub_prefix, subdispatchers in dispatcher.subdispatchers.items():
        for sub_disp in subdispatchers:
            lst.extend(dispatcher_methods(sub_disp, sub_prefix))
    return lst


def list_public_rpc_methods(dispatcher):
    # to be launched only once at at startup
    for name in sorted(dispatcher_methods(dispatcher)):
        if name not in public_methods:
            public_methods.append(name)


def available_methods():
    return deepcopy(public_methods)
