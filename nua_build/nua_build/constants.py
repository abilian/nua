from pathlib import Path

from .version import __version__

NUA_BUILDER_TAG = f"nua-builder:{__version__}"
NUA_PYTHON_TAG = f"nua-python:{__version__}"
BUILD = "nua_build_dir"
_folder = Path(__file__).parent
DOCKERFILE_PYTHON = _folder / "dockerfiles" / "Dockerfile_nua_python"
DOCKERFILE_BUILDER = _folder / "dockerfiles" / "Dockerfile_nua_builder"
MYSELF_DIR = _folder.parent
DEFAULTS_DIR = _folder / "defaults"
NUA_CONFIG = "nua-config.toml"
# in docker:
NUA_BUILD_PATH = "/nua/build"
NUA_APP_PATH = "/nua/app"
NUA_METADATA_PATH = "/nua/metadata"
NUA_SCRIPTS_PATH = "/nua/scripts"
