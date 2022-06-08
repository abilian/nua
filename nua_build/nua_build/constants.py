from pathlib import Path

from .version import __version__

NUA_BASE_TAG = f"nua-base:{__version__}"
NUA_MIN_TAG = f"nua-min:{__version__}"
BUILD = "_build"
DOCKERFILE_MIN = Path(__file__).parent / "dockerfiles" / "Dockerfile_pip_minimal"
DOCKERFILE_NUA_BASE = Path(__file__).parent / "dockerfiles" / "Dockerfile_nua_base"
MYSELF_DIR = Path(__file__).parent.parent
DEFAULTS_DIR = Path(__file__).parent / "defaults"
NUA_CONFIG = "nua-config.toml"
# in docker:
NUA_BUILD_PATH = "/nua/build"
NUA_SCRIPTS_PATH = "/nua/scripts"
