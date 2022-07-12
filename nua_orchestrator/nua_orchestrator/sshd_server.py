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
from copy import deepcopy
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

from .keys_utils import parse_pub_key_content

logging.basicConfig()
paramiko.util.log_to_file("/tmp/nua_ssh.log", level="INFO")
logger = paramiko.util.get_logger("paramiko")

CMD_ALLOW = {"docker_list"}
_CMD_ALLOW_ONLY_ADMIN = {
    "user_count",
    "user_add",
    "user_list",
    "user_update",
    "user_pubkey",
    "user_delete",
}
CMD_ALLOW_ADMIN = deepcopy(CMD_ALLOW)
CMD_ALLOW_ADMIN.update(_CMD_ALLOW_ONLY_ADMIN)
KEEP_ALIVE = 30
MAX_CNX_DURATION = 3600

zmq_ctx = zmq.Context()


class NuaAuthError(FixedErrorMessageMixin, Exception):
    jsonrpc_error_code = -32000
    message = "Command not found or not authorized"


def rpc_call(request, rpc_port):
    transport = ZmqClientTransport.create(zmq_ctx, f"tcp://127.0.0.1:{rpc_port}")
    # logger.info(request.serialize())
    reply = transport.send_message(request.serialize(), expect_reply=True)
    return reply


def is_allowed_command(request, is_admin: bool) -> bool:
    # if is_admin:
    #     allowed_commands = CMD_ALLOW_ADMIN
    # else:
    #     allowed_commands = CMD_ALLOW
    # FIXME: while developping:
    allowed_commands = CMD_ALLOW_ADMIN
    method = request.method
    if method not in allowed_commands:
        logger.info(f"Requested method is not in allowed commands: {method}")
        return False
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

    # No session used
    # def check_channel_request(self, kind, chanid):
    #     if kind == "session":
    #         return paramiko.OPEN_SUCCEEDED
    #     return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

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
