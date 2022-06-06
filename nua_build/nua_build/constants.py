from pathlib import Path

from .version import __version__

NUA_TAG = f"nua_base:{__version__}"
BUILD = "_build"
DOCKER_FILE = Path(__file__).parent / "nua_docker_file" / "Dockerfile"
MYSELF_DIR = Path(__file__).parent.parent
DEFAULTS_DIR = Path(__file__).parent / "defaults"
NUA_CONFIG = "nua-config.toml"
