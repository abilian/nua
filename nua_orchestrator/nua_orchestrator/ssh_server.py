"""SSH server for remote access of Nua cli
"""
import logging
import multiprocessing as mp
import socket
import sys
import threading
import traceback
from base64 import decodebytes
from os import chdir
from pathlib import Path
from time import sleep

import paramiko

config = {
    "host_key": Path(__file__).parent / "host_key" / "server_rsa",
    "auth_keys_dir": Path(__file__).parent / "auth_keys",
    "log_file": "/tmp/nua_ssh.log",
    "max_threads": 20,
}

logging.basicConfig()
paramiko.util.log_to_file(config["log_file"], level="INFO")
logger = paramiko.util.get_logger("paramiko")

host_key = paramiko.RSAKey(filename=str(config["host_key"]))


def method_from_key_type(key_type: str):
    meth = None
    if key_type == "ssh-rsa":
        meth = paramiko.RSAKey
    elif key_type.startswith("ecdsa-"):
        meth = paramiko.ECDSAKey
    elif key_type == "ssh-ed25519":
        meth = paramiko.Ed25519Key
    return meth


def parse_pub_key(key_type: str, key_data: str):
    "detect wich Paramiko method to use and return a valid key or None"
    key = None
    meth = method_from_key_type(key_type)
    if meth:
        key = meth(data=decodebytes(key_data.encode("ascii")))
        if key.get_bits() == 0:
            key = None
    return key


def parse_pub_key_content(content: str):
    parts = content.split(" ")
    if len(parts) < 2:
        # wrong format
        return None
    key_type = parts[0]
    key_data = parts[1]
    # no use of comment parts[2] of the key
    try:
        return parse_pub_key(key_type, key_data)
    except Exception:
        return None


def authorized_keys(folder: str = "") -> list:
    # maybe some cache here ?
    pub_keys = []
    if not folder:
        folder = Path(config["auth_keys_dir"])
    for path in folder.glob("*"):
        try:
            with open(path, encoding="utf8") as kfile:
                content = kfile.read()
        except OSError:
            continue
        key = parse_pub_key_content(content)
        if key:
            pub_keys.append(key)

    return pub_keys


class Server(paramiko.ServerInterface):
    """Class managing a ssh conenxion"""

    def __init__(self):
        self.event = threading.Event()

    def check_channel_request(self, kind, chanid):
        if kind == "session":
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_auth_publickey(self, username, key):
        if key in authorized_keys():
            return paramiko.AUTH_SUCCESSFUL
        return paramiko.AUTH_FAILED

    def get_allowed_auths(self, username):
        return "publickey"

    def check_channel_exec_request(self, channel, command):
        # This is the command we need to parse
        cmd = command[:1024].decode("utf8", "replace")
        logger.info(f"command: {cmd}")
        sleep(30)
        channel.send(f"{cmd} result\n")
        self.event.set()
        return True


def handler(client):
    try:
        transport = paramiko.Transport(client)
        transport.load_server_moduli()
        transport.add_server_key(host_key)
        server = Server()
        transport.start_server(server=server)
        server.event.wait()
        transport.close()
    except Exception as e:
        logging.error(f"Handler failed: {e}")
        tb_info = traceback.format_tb(sys.exc_info()[2], limit=2)
        data = tb_info[1].strip()
        logging.error(data)


def ssh_listener(config_arg):
    chdir(config_arg.read("nua", "ssh", "work_dir"))
    address = config_arg.read("nua", "ssh", "address")
    port = config_arg.read("nua", "ssh", "port")
    max_threads = config["max_threads"]
    logger.info(f"SSH server start at {address}:{port}")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((address, int(port)))
    except Exception as e:
        logger.error(f"Sock failed: {e}")
        tb_info = traceback.format_tb(sys.exc_info()[2], limit=2)
        data = tb_info[1].strip()
        logging.error(data)
        sys.exit(1)
    try:
        sock.listen()
    except Exception as e:
        logger.error(f"Listen failed: {e}")
        tb_info = traceback.format_tb(sys.exc_info()[2], limit=2)
        data = tb_info[1].strip()
        logging.error(data)
        sys.exit(1)

    while True:
        client, addr = sock.accept()
        if len(threading.enumerate()) > max_threads * 2:
            logging.info(f"Reach max_threads {max_threads}, close connection")
            client.close()
            continue
        logging.info(f"Connection of {addr}")
        cnx = threading.Thread(target=handler, args=(client,), daemon=True)
        cnx.start()


def start_ssh_server():
    proc = mp.Process(target=ssh_listener, args=(config,))
    proc.daemon = True
    proc.start()
