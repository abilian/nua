import socket
from contextlib import closing

from .. import config


def check_port_available(host: str, port: str, timeout: int = 1) -> bool:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        try:
            sock.bind((host, int(port)))
        except OSError:
            return False
    return True


def verify_ports_availability() -> None:
    """Verify that ports listed in the configuration are available."""
    seen = set()
    # registry
    port = config.read("nua", "registry", "local", "host_port")
    if port and not check_port_available("127.0.0.1", port):
        # raise ValueError("nua.registry.local: Registry port " f" {port} already in use")
        print(
            f"nua.registry.local: Registry port {port} already in use, will use this registry)"
        )
        # here check that maybe the registry container is still running, so
        # no actual problem
    seen.add(port)
    # # zmq rpc server
    # port = config.read("nua", "zmq", "port")
    # if port and (port in seen or not check_port_available("127.0.0.1", port)):
    #     raise ValueError(f"nua.zmq: RPC port {port} already in use")
