"""Key management with paramiko common to several packages."""
import io
from base64 import decodebytes
from typing import Any, Optional

import paramiko


def parse_private_rsa_key_content(content: str) -> Optional[paramiko.RSAKey]:
    """Parse a alleged RSA private key content.

    Returns:
        paramiko Key instance or None.
    """
    try:
        return paramiko.RSAKey(file_obj=io.StringIO(content))
    except paramiko.SSHException:
        return None


def method_from_key_type(key_type: str) -> Any:
    """Return the paramiko method relevant for a key type or None."""
    meth = None
    if key_type == "ssh-rsa":
        meth = paramiko.RSAKey
    elif key_type.startswith("ecdsa-"):
        meth = paramiko.ECDSAKey
    elif key_type == "ssh-ed25519":
        meth = paramiko.Ed25519Key
    return meth


def parse_pub_key(key_type: str, key_data: str) -> Any:
    """Detect wich Paramiko method for parsing and return a valid key or
    None."""
    key = None
    meth = method_from_key_type(key_type)
    if meth:
        key = meth(data=decodebytes(key_data.encode("ascii")))
        if key.get_bits() == 0:
            key = None
    return key


def is_private_key(key_content: str) -> bool:
    """Test if a key content can be a private key."""
    if "BEGIN OPENSSH PRIVATE KEY" in key_content:
        return True
    key = parse_private_rsa_key_content(key_content)
    if key and key.can_sign():
        return True
    return False


def parse_pub_key_content(key_content: str) -> Any:
    """Parse a alleged public key content (openSSH base64 format).

    Returns:
        paramiko Key instance or None.
    """
    parts = key_content.split(" ")
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
