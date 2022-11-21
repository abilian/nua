from pathlib import Path

from .version import __version__

CODE_URL = "https://github.com/abilian/nua/archive/refs/heads/main.zip"
# Ubuntu 22.04.1 "jammy" LTS with python3.10
# NUA_LINUX_BASE = "ubuntu:jammy-20220801"
NUA_LINUX_BASE = "ubuntu:jammy-20221003"

NUA_BUILDER_TAG = f"nua-builder:{__version__}"
NUA_PYTHON_TAG = f"nua-python:{__version__}"
NUA_WHEEL_DIR = Path(f"/var/tmp/nua_build_wheel_{__version__}")  # noqa S108

_folder = Path(__file__).parent
# DOCKERFILE_PYTHON = _folder / "dockerfiles" / "Dockerfile_nua_python"
DOCKERFILE_PYTHON = _folder / "dockerfiles" / "Dockerfile_nua_python_slim"
DOCKERFILE_BUILDER = _folder / "dockerfiles" / "Dockerfile_nua_builder_slim"
MYSELF_DIR = _folder.parent
DEFAULTS_DIR = _folder / "defaults"
NUA_CONFIG = "nua-config.toml"
# in docker:
NUA_BUILD_PATH = "/nua/build"
NUA_APP_PATH = "/nua/app"
NUA_METADATA_PATH = "/nua/metadata"
NUA_SCRIPTS_PATH = "/nua/scripts"
