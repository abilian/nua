from .version import __version__

NUA_PYTHON_TAG = f"nua-python:{__version__}"
NUA_BUILDER_TAG = f"nua-builder:{__version__}"
NUA_BUILDER_NODE_TAG16 = f"nua-builder-nodejs16:{__version__}"

NUA_CONFIG = "nua-config.toml"
# in docker:
NUA_BUILD_PATH = "/nua/build"
NUA_APP_PATH = "/nua/app"
NUA_METADATA_PATH = "/nua/metadata"
NUA_SCRIPTS_PATH = "/nua/scripts"
