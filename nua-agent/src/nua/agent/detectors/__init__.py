"""Base class for detect and install project."""
from .python_source import PythonSource
from .python_wheels import PythonWheels

__all__ = ["PythonSource", "PythonWheels"]
