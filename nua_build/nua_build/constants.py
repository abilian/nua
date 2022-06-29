from pathlib import Path

from .version import __version__

NUA_BUILDER_TAG = f"nua-builder:{__version__}"
NUA_PYTHON_TAG = f"nua-python:{__version__}"
BUILD = "_build"
_folder = Path(__file__).parent
DOCKERFILE_PYTHON = _folder / "dockerfiles" / "Dockerfile_nua_python"
DOCKERFILE_BUILDER = _folder / "dockerfiles" / "Dockerfile_nua_builder"
MYSELF_DIR = _folder.parent
DEFAULTS_DIR = _folder / "defaults"
NUA_CONFIG = "nua-config.toml"
# in docker:
NUA_BUILD_PATH = "/nua/build"
NUA_SCRIPTS_PATH = "/nua/scripts"
