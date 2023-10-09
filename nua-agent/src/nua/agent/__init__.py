"""Agent libray of Nua, embedded in each Nua Docker image."""

# Version of module available at first level, __version__ actually
# computed from pyproject data in version.py module

# import packaging  # to ensure the module is installed

from .version import __version__  # noqa: F401

# assert packaging  # to avoid flake8 warning
