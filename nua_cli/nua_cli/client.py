from pathlib import Path

import paramiko

from .config import config


def remote_exec(cmd="ls"):
    conf = config["ssh"]
    ssh = paramiko.SSHClient()
    if conf.get("auto_add_policy"):
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    pub_key = Path(conf["public_key"]).expanduser()
    if pub_key.exists():
        # assuming a RSA key
        pkey = paramiko.RSAKey(filename=pub_key)
        ssh.connect(
            conf["remote_address"],
            port=conf["remote_port"],
            username="nua",
            pkey=pkey,
            look_for_keys=False,
        )
    else:
        ssh.connect(
            conf["remote_address"],
            port=conf["remote_port"],
            username="nua",
            look_for_keys=True,
        )
    _stdin, stdout, _stderr = ssh.exec_command(cmd)
    output = stdout.read()
    ssh.close()
    print(output)
