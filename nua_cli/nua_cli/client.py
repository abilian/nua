from pathlib import Path

import paramiko

from .config import config


def remote_exec(cmd="ls"):
    conf = config["ssh"]
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    if conf.get("auto_add_policy"):
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    priv_key = Path(conf["private_key"]).expanduser()
    if priv_key.exists():
        # assuming a RSA key
        pkey = paramiko.RSAKey(filename=priv_key)
        client.connect(
            hostname=conf["remote_address"],
            port=conf["remote_port"],
            username="nua",
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
            username="nua",
            look_for_keys=True,
        )
    _stdin, stdout, _stderr = client.exec_command(cmd)
    output = stdout.read()
    client.close()
    print(output)
