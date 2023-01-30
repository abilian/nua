# for now let provide commands at first level:
from .config import config  # noqa: F401
from .register_plugin import register_db_plugins
from .version import __version__  # noqa: F401

register_db_plugins()
