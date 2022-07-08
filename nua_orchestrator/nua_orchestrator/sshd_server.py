"""SSHD server for remote access (via Nua cli).

Server uses the global_request feature, so allowing only our specific
protocol on the SSH channel.
"""
import io

# for check of username:
# /^[_.A-Za-z0-9][-\@_.A-Za-z0-9]*\$?$/
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
import zmq
from tinyrpc.protocols.jsonrpc import (
    FixedErrorMessageMixin,
    JSONRPCParseError,
    JSONRPCProtocol,
)
from tinyrpc.transports.zmq import ZmqClientTransport

logging.basicConfig()
paramiko.util.log_to_file("/tmp/nua_ssh.log", level="INFO")
logger = paramiko.util.get_logger("paramiko")

CMD_ALLOW = {"docker_list": {}}
_CMD_ALLOW_ONLY_ADMIN = {}
CMD_ALLOW_ADMIN = CMD_ALLOW.update(_CMD_ALLOW_ONLY_ADMIN)
KEEP_ALIVE = 30
MAX_CNX_DURATION = 3600

zmq_ctx = zmq.Context()


class NuaAuthError(FixedErrorMessageMixin, Exception):
    jsonrpc_error_code = -32000
    message = "Command not found or not authorized"


def rpc_call(request, rpc_port):
    transport = ZmqClientTransport.create(zmq_ctx, f"tcp://127.0.0.1:{rpc_port}")
    reply = transport.send_message(request.serialize(), expect_reply=True)
    return reply


def is_allowed_command(request, is_admin: bool) -> bool:
    if is_admin:
        allowed_commands = CMD_ALLOW_ADMIN
    else:
        allowed_commands = CMD_ALLOW
    method = request.method
    # second_param = args[1] if len[args] > 1 else ""
    if method not in allowed_commands:
        logger.info(f"Requested method is not in allowed commands: {method}")
        return False
    # second_level = allowed_commands[first_param]
    # if second_level and second_param not in second_level:
    #     return False
    return True


def exec_nua_command(cmd: str, username: str, is_admin: bool, rpc_port: int) -> str:
    logger.info(f"exec_nua_command(): cmd: {cmd}, user: {username}, admin: {is_admin}")
    response = rpc_response(cmd, is_admin, rpc_port)
    str_response = response.decode("utf8", "replace")
    logger.info(f"resp: {str_response}")
    return str_response


def rpc_response(cmd, is_admin, rpc_port):
    # logger.info("in rpc_command()")
    cmd = cmd.strip()
    bcmd = cmd.encode("utf8", "replace")
    proto = JSONRPCProtocol()
    try:
        request = proto.parse_request(bcmd)
    except JSONRPCParseError:
        logger.info("rpc_command: parsing of request failed")
        err = NuaAuthError()
        return err.error_respond().serialize()
    if not is_allowed_command(request, is_admin):
        err = NuaAuthError()
        return err.error_respond().serialize()
    return rpc_call(request, rpc_port)


# def load_host_key(host_key_path):
#     path = Path(host_key_path)
#     if not path.exists():
#         path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
#         key = paramiko.RSAKey.generate(2048)
#         key.write_private_key_file(path)
#     # assuming it's a rsa key
#     return paramiko.RSAKey(filename=path)


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
    """detect wich Paramiko method to use and return a valid key or None."""
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
    # fixme: change this, need as parameters:
    #  - alleged username
    #  - key content
    # goto auth_keys_dir/username,
    # check locally that some key exists
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
    """Class managing a ssh connection and granted rights."""

    def __init__(self, auth_keys_dir: str, admin_auth_keys_dir: str, rpc_port: int):
        # self.event = threading.Event()
        self.auth_keys_dir = auth_keys_dir
        self.admin_auth_keys_dir = admin_auth_keys_dir
        self.is_admin = False
        self.username = ""
        self.rpc_port = rpc_port

    def check_channel_request(self, kind, chanid):
        if kind == "session":
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_auth_publickey(self, username, key):
        self.username = username
        if key in authorized_keys(self.admin_auth_keys_dir):
            self.is_admin = True
            return paramiko.AUTH_SUCCESSFUL
        if key in authorized_keys(self.auth_keys_dir):
            return paramiko.AUTH_SUCCESSFUL
        return paramiko.AUTH_FAILED

    def get_allowed_auths(self, username):
        return "publickey"

    def check_global_request(self, kind, msg):
        if kind != "nua" or not msg:
            return False
        # mkind = msg.get_string()  # a paramiko bug ?
        msg.rewind()
        _kind = msg.get_string()
        _byte = msg.get_byte()
        bcmd = msg.get_string()
        cmd = bcmd.decode("utf8", "ignore")
        result = exec_nua_command(cmd, self.username, self.is_admin, self.rpc_port)
        # self.event.set()
        return ("nua", result.encode("utf8", "ignore"))


def handler(client, conf):
    server_key = paramiko.RSAKey(file_obj=io.StringIO(conf["host_key"]))
    auth_keys_dir = conf["auth_keys_dir"]
    admin_auth_keys_dir = conf["admin_auth_keys_dir"]
    rpc_port = conf["rpc_port"]
    try:
        transport = paramiko.Transport(client)
        # transport.load_server_moduli()  # useless for paramiko as client
        transport.add_server_key(server_key)
        transport.set_keepalive(KEEP_ALIVE)
        server = Server(auth_keys_dir, admin_auth_keys_dir, rpc_port)
        transport.start_server(server=server)
        count_down = MAX_CNX_DURATION
        while count_down > 0:
            if not transport.is_active():
                return
            count_down -= 1
            sleep(1)
        transport.close()
    except Exception as e:
        logger.error(f"Handler failed: {e}")
        tb_info = traceback.format_tb(sys.exc_info()[2], limit=2)
        data = tb_info[1].strip()
        logger.error(data)


def sshd(conf):
    address = conf["address"]
    port = conf["port"]
    logger.info(f"SSH server start at {address}:{port}")
    chdir(conf["work_dir"])
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((address, int(port)))
        sock.listen(5)
    except Exception as e:
        logger.error(f"Sshd: {e}")
        tb_info = traceback.format_tb(sys.exc_info()[2], limit=2)
        data = tb_info[1].strip()
        logger.error(data)
        sys.exit(1)

    while True:
        client, addr = sock.accept()
        logger.info(f"Connection from {addr}")
        cnx = threading.Thread(target=handler, args=(client, conf), daemon=True)
        cnx.start()


def start_sshd_server(config):
    logger.info("start_ssh_server")
    conf = {
        "host_key": config.read("nua", "host", "host_priv_key_blob"),
        "address": config.read("nua", "ssh", "address"),
        "port": config.read("nua", "ssh", "port"),
        "work_dir": config.read("nua", "ssh", "work_dir"),
        "auth_keys_dir": config.read("nua", "ssh", "auth_keys_dir") or "",
        "admin_auth_keys_dir": config.read("nua", "ssh", "admin_auth_keys_dir") or "",
        "rpc_port": config.read("nua", "zmq", "port"),
    }
    proc = mp.Process(
        target=sshd,
        args=(conf,),
        daemon=True,
    )
    proc.start()
    return True
