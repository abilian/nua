from tinyrpc.dispatch import public

from ..rpc_utils import register_methods, rpc_trace


class RPCTestMethods:
    def __init__(self, config):
        self.config = config

    @public
    @rpc_trace
    def add(self, a, b):
        return a + b

    @public
    @rpc_trace
    def divide(self, a, b):
        return a / b


register_methods(RPCTestMethods, "test_")
