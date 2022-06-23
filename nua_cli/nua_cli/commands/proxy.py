import os
from functools import wraps

import zmq
from tinyrpc import RPCClient
from tinyrpc.protocols.jsonrpc import JSONRPCError, JSONRPCProtocol
from tinyrpc.transports.zmq import ZmqClientTransport
from typer import Abort, secho

NUA_ADDRESS = os.environ.get("NUA_ADDRESS") or "127.0.0.1"
NUA_PORT = os.environ.get("NUA_PORT") or "5001"

zmq_ctx = zmq.Context()


def get_rpc_client():
    rpc_client = RPCClient(
        JSONRPCProtocol(),
        ZmqClientTransport.create(zmq_ctx, f"tcp://{NUA_ADDRESS}:{NUA_PORT}"),
    )
    return rpc_client


def get_proxy():
    return get_rpc_client().get_proxy()


def abort_rpc_error(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except JSONRPCError as e:
            # print("Error:", e._jsonrpc_error_code, e.message)
            secho(f"Error: {e.message}", bold=True, err=True)
            if hasattr(e, "data"):
                secho(f"Data: {e.data}", err=True)
            Abort(2)

    return wrapper
