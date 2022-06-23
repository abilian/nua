from tinyrpc.dispatch import public

from ..utils import rpc_trace


class RPCPluginTest:
    prefix = "plugin_"

    def __init__(self, config: dict):
        self.config = config

    @public
    @rpc_trace
    def multiply(self, a, b):
        return a * b

    @public
    @rpc_trace
    def substract(self, a, b):
        return a - b
