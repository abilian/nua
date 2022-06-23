import sys
import traceback
from functools import wraps

from tinyrpc.protocols.jsonrpc import JSONRPCServerError


def rpc_trace(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except Exception as e:
            tb_info = traceback.format_tb(sys.exc_info()[2], limit=2)
            raise JSONRPCServerError(e, data=tb_info[1].strip())

    return wrapper
