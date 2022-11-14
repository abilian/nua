import io
import sys
from pathlib import Path
from pprint import pformat

from nua.lib.common.panic import error
from nua_orchestrator.db import store
from nua_orchestrator.db_setup import setup_db
from paramiko import RSAKey


def generate_rsa_host_key(bits=4096) -> RSAKey:
    """Generate a new private RSA key.

    This factory function can be used to generate a new host key or
    authentication key.
    """
    key = RSAKey.generate(bits)
    return key


def private_key_blob_from_key(key: RSAKey, password: str = None) -> str:
    """Write an SSH2-format private key file in a form that can be read by
    paramiko or openssh.

    If no password is given, the key is written in a trivially-encoded
    format (base64) which is completely insecure.  If a password is
    given, DES-EDE3-CBC is used.
    """
    output = io.StringIO()
    key.write_private_key(output, password)
    content = output.getvalue()
    output.close()
    return content


def print_local_nua_config():
    setup_db()
    settings = store.installed_nua_settings()
    print(pformat(settings))


def set_new_host_key():
    """Generate a random RSA key (4096 bits) and store it in the nua DB
    settings as "host.host_priv_key_blob"."""
    print("Generating RSA key (4096 bits) for Nua host...")
    new_key = generate_rsa_host_key()
    blob = private_key_blob_from_key(new_key)
    setup_db()
    settings = store.installed_nua_settings()
    settings["host"]["host_priv_key_blob"] = blob
    store.set_nua_settings(settings)
    print("Done.")


def set_new_host_key_from_file():
    """Read private RSA ey from file and store it in the nua DB settings as
    "host.host_priv_key_blob"."""
    print("Store RSA key in Nua host...")
    path = Path(sys.argv[1]).expanduser()
    if not path.exists():
        error(f"File not found (or not access granted): {str(path)}")
    key = RSAKey(filename=path)
    blob = private_key_blob_from_key(key)
    setup_db()
    settings = store.installed_nua_settings()
    settings["host"]["host_priv_key_blob"] = blob
    store.set_nua_settings(settings)
    print("Done.")
