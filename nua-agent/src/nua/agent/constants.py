from .version import __version__

NUA_PYTHON_TAG = f"nua-python:{__version__}"
NUA_BUILDER_TAG = f"nua-builder:{__version__}"

NUA_CONFIG_STEM = "nua-config"
NUA_CONFIG_EXT = ("json", "toml", "yaml", "yml")
# in docker:
NUA_BUILD_PATH = "/nua/build"
NUA_APP_PATH = "/nua/app"
NUA_METADATA_PATH = "/nua/metadata"
NUA_SCRIPTS_PATH = "/nua/scripts"
