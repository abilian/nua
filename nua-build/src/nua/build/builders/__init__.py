"""Builder class, core of build process.

Builder instance maintains config and other state information during build.

Typical use::

    builder = get_builder(config_file)
    builder.run()
"""

from .base import Builder, BuilderError
from .factory import get_builder

__all__ = ["Builder", "BuilderError", "get_builder"]
