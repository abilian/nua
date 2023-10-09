from .version import __version__

# NB: this assumes that all the nua packages have the same version
NUA_PYTHON_TAG = f"nua-python:{__version__}"
NUA_BUILDER_TAG = f"nua-builder:{__version__}"

NUA_CONFIG_STEM = "nua-config"
NUA_CONFIG_EXT = ("json", "toml", "yaml", "yml")

# In the container:
NUA_BUILD_PATH = "/nua/build"
NUA_APP_PATH = "/nua/app"
NUA_METADATA_PATH = "/nua/metadata"
NUA_SCRIPTS_PATH = "/nua/scripts"


def nua_config_names():
    for suffix in NUA_CONFIG_EXT:
        yield f"{NUA_CONFIG_STEM}.{suffix}"
