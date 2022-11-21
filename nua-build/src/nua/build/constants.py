from pathlib import Path

from .version import __version__

_folder = Path(__file__).parent
MYSELF_DIR = _folder.parent
DEFAULTS_DIR = _folder / "defaults"
NUA_CONFIG = "nua-config.toml"
# in docker:
NUA_BUILD_PATH = "/nua/build"
NUA_APP_PATH = "/nua/app"
NUA_METADATA_PATH = "/nua/metadata"
NUA_SCRIPTS_PATH = "/nua/scripts"
