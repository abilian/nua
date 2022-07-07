import multiprocessing as mp

import zmq
from tinyrpc.protocols.jsonrpc import JSONRPCProtocol
from tinyrpc.server import RPCServer
from tinyrpc.transports.zmq import ZmqServerTransport

from .dispatcher import register_methods
from .server_utils.mini_log import log, log_me

zmq_ctx = zmq.Context()


def log_rpc_request(direction, context, message):
    message = message.decode("utf8", errors="replace")
    if len(message) > 1021:
        message = message[:1021] + "..."
    log(f"{direction} {message}")


def zmq_rpc_server(config):
    address = config.read("nua", "zmq", "address")
    port = config.read("nua", "zmq", "port")
    log_me(f"RPC server start at {address}:{port}")
    dispatcher = register_methods(config)
    transport = ZmqServerTransport.create(zmq_ctx, f"tcp://{address}:{port}")
    rpc_server = RPCServer(transport, JSONRPCProtocol(), dispatcher)
    rpc_server.trace = log_rpc_request
    rpc_server.serve_forever()


def start_zmq_rpc_server(config):
    proc = mp.Process(target=zmq_rpc_server, args=(config,))
    proc.daemon = True
    proc.start()
