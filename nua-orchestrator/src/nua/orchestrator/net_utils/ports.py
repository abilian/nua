import socket
from contextlib import closing


def check_port_available(host: str, port: str, timeout: int = 1) -> bool:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        try:
            sock.bind((host, int(port)))
        except OSError:
            return False
    return True
