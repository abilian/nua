from pathlib import Path

from .version import __version__

CODE_URL = "https://github.com/abilian/nua/archive/refs/heads/main.zip"
# Ubuntu 22.04.1 "jammy" LTS with python3.10
# NUA_LINUX_BASE = "ubuntu:jammy-20220801"
NUA_LINUX_BASE = "ubuntu:jammy-20221003"

NUA_BUILDER_TAG = f"nua-builder:{__version__}"
NUA_PYTHON_TAG = f"nua-python:{__version__}"

_folder = Path(__file__).parent
# DOCKERFILE_PYTHON = _folder / "dockerfiles" / "Dockerfile_nua_python"
DOCKERFILE_PYTHON = _folder / "dockerfiles" / "Dockerfile_nua_python_slim"
DOCKERFILE_BUILDER = _folder / "dockerfiles" / "Dockerfile_nua_builder_slim"
