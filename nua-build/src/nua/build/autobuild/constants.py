from ..version import __version__

CODE_URL = "https://github.com/abilian/nua/archive/refs/heads/main.zip"

# Ubuntu 22.04.1 "jammy" LTS with python3.10
NUA_LINUX_BASE = "ubuntu:jammy-20230816"

NUA_PYTHON_TAG = f"nua-python:{__version__}"

DOCKERFILE_PYTHON = "Dockerfile_nua_python_slim"
DOCKERFILE_BUILDER = "Dockerfile_nua_builder_slim"
