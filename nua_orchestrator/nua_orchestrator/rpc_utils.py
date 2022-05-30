from functools import wraps
import traceback
import sys
from importlib import import_module
from pathlib import Path
from copy import deepcopy
from tinyrpc.protocols.jsonrpc import JSONRPCServerError

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


def register_rpc_modules():
    folder = Path(__file__).parent / "methods"
    base = __name__.split(".")[:-1]
    base.append("methods")
    base_name = ".".join(base)
    for module_file in folder.glob("*.py"):
        if module_file.name.startswith("_"):
            continue
        mod_name = module_file.stem
        import_module(f"{base_name}.{mod_name}")


def register_methods(klass, prefix):
    if klass not in registered_classes:
        registered_classes.append((klass, prefix))


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
