import multiprocessing as mp

import zmq
from tinyrpc.dispatch import RPCDispatcher
from tinyrpc.protocols.jsonrpc import JSONRPCProtocol
from tinyrpc.server import RPCServer
from tinyrpc.transports.zmq import ZmqServerTransport

from .rpc_utils import (
    available_methods,
    list_public_rpc_methods,
    register_rpc_modules,
    registered_classes,
)
from .server_utils.mini_log import log


def start_zmq_rpc_server(config):
    proc = mp.Process(target=zmq_rpc_server, args=(config,))
    proc.daemon = True
    proc.start()


def zmq_rpc_server(config):
    address = config["zmq"]["address"]
    port = config["zmq"]["port"]
    ctx = zmq.Context()

    register_rpc_modules()
    dispatcher = RPCDispatcher()
    for klass, prefix in registered_classes:
        obj = klass(config)
        log("loading class", klass.__name__, "with prefix'", prefix, "'")
        dispatcher.register_instance(obj, prefix)

    list_public_rpc_methods(dispatcher)
    log("registered methods:")
    for name in available_methods():
        log("    ", name)

    transport = ZmqServerTransport.create(ctx, f"tcp://{address}:{port}")
    rpc_server = RPCServer(transport, JSONRPCProtocol(), dispatcher)
    rpc_server.serve_forever()
