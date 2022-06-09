from pathlib import Path

from .version import __version__

NUA_BASE_TAG = f"nua-base:{__version__}"
NUA_MIN_TAG = f"nua-min:{__version__}"
BUILD = "_build"
_folder = Path(__file__).parent
DOCKERFILE_MIN = _folder / "dockerfiles" / "Dockerfile_pip_minimal"
DOCKERFILE_NUA_BASE = _folder / "dockerfiles" / "Dockerfile_nua_base"
MYSELF_DIR = _folder.parent
DEFAULTS_DIR = _folder / "defaults"
NUA_CONFIG = "nua-config.toml"
# in docker:
NUA_BUILD_PATH = "/nua/build"
NUA_SCRIPTS_PATH = "/nua/scripts"
