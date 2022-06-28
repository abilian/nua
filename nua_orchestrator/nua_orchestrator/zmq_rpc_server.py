import multiprocessing as mp
import sys
import traceback

import zmq
from tinyrpc.dispatch import RPCDispatcher
from tinyrpc.protocols.jsonrpc import JSONRPCProtocol
from tinyrpc.server import RPCServer
from tinyrpc.transports.zmq import ZmqServerTransport

from . import config
from .rpc_utils import (
    available_methods,
    list_public_rpc_methods,
    register_rpc_local_methods,
    register_rpc_plugins,
    registered_classes,
)
from .server_utils.mini_log import log, log_me

zmq_ctx = zmq.Context()


def start_zmq_rpc_server():
    proc = mp.Process(target=zmq_rpc_server, args=(config,))
    proc.daemon = True
    proc.start()


def log_rpc_request(direction, context, message):
    message = message.decode("utf8", errors="replace")
    if len(message) > 1021:
        message = message[:1021] + "..."
    log(f"{direction} {message}")


def zmq_rpc_server(config_arg):
    address = config_arg.read("nua", "zmq", "address")
    port = config_arg.read("nua", "zmq", "port")
    log_me(f"RPC server start at {address}:{port}")
    register_rpc_local_methods()
    register_rpc_plugins(config_arg.read("nua", "rpc", "plugin"))
    dispatcher = RPCDispatcher()
    for klass in registered_classes:
        try:
            obj = klass(config_arg.read("nua"))
            log("loading class", klass.__name__, "with prefix'", klass.prefix, "'")
            dispatcher.register_instance(obj, obj.prefix)
        except Exception as e:
            log_me(f"Error while register class {klass.__name__}")
            log_me(e)
            tb_info = traceback.format_tb(sys.exc_info()[2], limit=2)
            data = tb_info[1].strip()
            log_me(data)

    list_public_rpc_methods(dispatcher)
    log("registered methods:")
    for name in available_methods():
        log("    ", name)

    transport = ZmqServerTransport.create(zmq_ctx, f"tcp://{address}:{port}")
    rpc_server = RPCServer(transport, JSONRPCProtocol(), dispatcher)
    rpc_server.trace = log_rpc_request
    rpc_server.serve_forever()
