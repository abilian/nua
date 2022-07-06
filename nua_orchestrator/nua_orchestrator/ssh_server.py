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

from . import config
from .zmq_rpc_server import get_dispatcher

# from .main import app

logging.basicConfig()
paramiko.util.log_to_file("/tmp/nua_ssh.log", level="INFO")
logger = paramiko.util.get_logger("paramiko")

CMD_ERR = "Command not found or not authorized"
CMD_ALLOW = {"registry": {"list"}}
CMD_ADMIN_ALLOW = CMD_ALLOW.update({})


def run_nua_command(args: list, is_admin: bool) -> str:
    dispatcher = get_dispatcher(config)
    cmd = " ".join(args)
    return "test" + cmd
    # result = runner.invoke(app, cmd)
    # if result.exit_code == 0:
    #     return result.stdout
    # else:
    #     return result.stdout + result.stderr


def is_allowed_command(args: list, is_admin: bool) -> bool:
    if is_admin:
        allowed_commands = CMD_ADMIN_ALLOW
    else:
        allowed_commands = CMD_ALLOW
    first_param = args[0]
    second_param = args[1] if len(args) > 1 else ""
    if first_param not in allowed_commands:
        return False
    second_level = allowed_commands[first_param]
    if second_level and second_param not in second_level:
        return False
    return True


def apply_nua_command(cmd: str, is_admin: bool) -> str:
    args = cmd.split()
    if not args:
        return CMD_ERR
    if not is_allowed_command(args, is_admin):
        return CMD_ERR
    return run_nua_command(args, is_admin)


def load_host_key(host_key_path):
    path = Path(host_key_path)
    if not path.exists():
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        key = paramiko.RSAKey.generate(2048)
        key.write_private_key_file(path)
    # assuming it's a rsa key
    return paramiko.RSAKey(filename=path)


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


def authorized_keys(auth_keys_dir: str) -> list:
    # maybe some cache here ?
    pub_keys = []
    folder = Path(auth_keys_dir)
    if not folder.exists():
        folder.mkdir(mode=0o700, parents=True, exist_ok=True)
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

    def __init__(self, auth_keys_dir: str, admin_auth_keys_dir: str):
        self.event = threading.Event()
        self.auth_keys_dir = auth_keys_dir
        self.admin_auth_keys_dir = admin_auth_keys_dir
        self.is_admin = False

    def check_channel_request(self, kind, chanid):
        if kind == "session":
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_auth_publickey(self, username, key):
        if key in authorized_keys(self.admin_auth_keys_dir):
            self.is_admin = True
            return paramiko.AUTH_SUCCESSFUL
        if key in authorized_keys(self.auth_keys_dir):
            return paramiko.AUTH_SUCCESSFUL
        return paramiko.AUTH_FAILED

    def get_allowed_auths(self, username):
        return "publickey"

    def check_channel_exec_request(self, channel, command):
        # This is the command we need to parse
        cmd = command[:2048].decode("utf8", "replace")
        logger.info(f"command: {cmd}")
        result = apply_nua_command(cmd, self.is_admin)
        channel.send(f"{result}\n")
        self.event.set()
        return True


def handler(client, host_key_path: str, auth_keys_dir: str, admin_auth_keys_dir: str):
    try:
        transport = paramiko.Transport(client)
        transport.load_server_moduli()
        transport.add_server_key(load_host_key(host_key_path))
        server = Server(auth_keys_dir, admin_auth_keys_dir)
        transport.start_server(server=server)
        server.event.wait()
        transport.close()
    except Exception as e:
        logging.error(f"Handler failed: {e}")
        tb_info = traceback.format_tb(sys.exc_info()[2], limit=2)
        data = tb_info[1].strip()
        logging.error(data)


def ssh_listener(config_arg):
    address = config_arg.read("nua", "ssh", "address")
    port = config_arg.read("nua", "ssh", "port")
    logger.info(f"SSH server start at {address}:{port}")
    chdir(config_arg.read("nua", "ssh", "work_dir"))
    host_key_path = config_arg.read("nua", "ssh", "host_key")
    auth_keys_dir = config_arg.read("nua", "ssh", "auth_keys_dir") or ""
    admin_auth_keys_dir = config_arg.read("nua", "ssh", "admin_auth_keys_dir") or ""
    max_threads = config_arg.read("nua", "ssh", "max_threads") or 20
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
        cnx = threading.Thread(
            target=handler,
            args=(client, host_key_path, auth_keys_dir, admin_auth_keys_dir),
            daemon=True,
        )
        cnx.start()


def start_ssh_server(config):
    proc = mp.Process(target=ssh_listener, args=(config,))
    proc.daemon = True
    proc.start()
