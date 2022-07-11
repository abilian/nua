import json
from pathlib import Path

import paramiko
from tinyrpc.protocols.jsonrpc import JSONRPCProtocol

from .config import config


def remote_exec(json_rpc_cmd: str) -> dict:
    conf = config["ssh"]
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    # FIXME: using AutoAddPolicy() while under development.
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    # client.set_missing_host_key_policy(paramiko.WarningPolicy())
    priv_key = Path(conf["private_key"]).expanduser()
    if priv_key.exists():
        # assuming a RSA key
        pkey = paramiko.RSAKey(filename=priv_key)
        client.connect(
            hostname=conf["remote_address"],
            port=conf["remote_port"],
            username=conf["username"],
            pkey=pkey,
            # paramiko dont accept this, so:
            disabled_algorithms={"pubkeys": ["rsa-sha2-256", "rsa-sha2-512"]},
            timeout=10,
            look_for_keys=False,
        )
    else:
        # paramiko seems broken there
        client.connect(
            conf["remote_address"],
            port=conf["remote_port"],
            username=conf["username"],
            look_for_keys=True,
        )
    transport = client.get_transport()
    response_msg = transport.global_request(
        "nua", (json_rpc_cmd.encode("utf8", "ignore"),)
    )
    client.close()
    _dummy = response_msg.get_string()
    content = response_msg.get_string()
    result = content.decode("utf8", "replace")
    return json.loads(result)


def ssh_request(method: str, request_dict: dict = None):
    proto = JSONRPCProtocol()
    if request_dict:
        request = proto.create_request(method, [request_dict])
    else:
        request = proto.create_request(method)
    json_rpc_cmd = request.serialize().decode("utf8", "replace")
    response = remote_exec(json_rpc_cmd)
    if "result" in response:
        return response["result"]
    else:
        print(response["error"])
        return None
