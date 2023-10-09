import json
import os
import shutil
import socket
from pathlib import Path

from nua.lib.panic import warning
from nua.lib.shell import sh

from nua.orchestrator.search_cmd import image_available_locally

os.environ["NUA_CERTBOT_TEST"] = "1"
os.environ["NUA_CERTBOT_VERBOSE"] = "1"


def fetch_environment() -> dict:
    record = {}
    _domainame(record)
    return record


def _domainame(record: dict):
    domain_name = os.environ.get("NUA_DOMAIN_NAME", "")
    if not domain_name:
        domain_name = socket.gethostname()
        warning("NUA_DOMAIN_NAME is not set.")
        domain_name = socket.gethostname()
    record["domain_name"] = domain_name


def ensure_docker_image(path: Path):
    deploy_conf = json.loads((path / "deploy.json").read_text(encoding="utf8"))
    app_name = deploy_conf["site"][0]["image"]
    if not image_available_locally(app_name):
        warning(f"Build of image '{app_name}' required'")
        build_image(path / "app")


def build_image(path: Path):
    check_nua_build_installation()
    cmd = f"sudo nua-build -v {path}"
    sh(cmd)


def check_nua_build_installation():
    if shutil.which("nua-build"):
        return
    warning("Installing 'nua-build'")
    cmd = "pip install -e ../../nua-build"
    sh(cmd)
