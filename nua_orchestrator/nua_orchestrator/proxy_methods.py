import zmq
from tinyrpc import RPCClient
from tinyrpc.protocols.jsonrpc import JSONRPCProtocol
from tinyrpc.transports.zmq import ZmqClientTransport

from . import config


def get_rpc_client():
    address = config.get("nua", "zmq", "address")
    port = config.get("nua", "zmq", "port")
    ctx = zmq.Context()
    rpc_client = RPCClient(
        JSONRPCProtocol(),
        ZmqClientTransport.create(ctx, f"tcp://{address}:{port}"),
    )
    return rpc_client


def get_proxy():
    return get_rpc_client().get_proxy()


def rpc_methods():
    proxy = get_proxy()
    return proxy.rpc_methods()
