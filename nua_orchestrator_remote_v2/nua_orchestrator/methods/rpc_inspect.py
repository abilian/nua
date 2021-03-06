from tinyrpc.dispatch import public

from ..rpc_utils import available_methods, register_methods, rpc_trace


class RPCInspect:
    prefix = "rpc_"

    def __init__(self, config: dict):
        self.config = config

    @public
    @rpc_trace
    def methods(self):
        return "\n".join(available_methods()) + "\n"


register_methods(RPCInspect)
