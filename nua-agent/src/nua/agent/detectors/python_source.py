"""Auto install Python project."""
from pathlib import Path

from nua.lib.actions import build_python

from ..auto_install import register_detector
from .base_detector import BaseDetector


class PythonSource(BaseDetector):
    message: str = "Python source project"
    priority: int = 100

    @classmethod
    def detect(cls) -> bool:
        root = Path(".").resolve()
        python_project_files = ("requirements.txt", "setup.py", "pyproject.toml")
        return any((root / f).exists() for f in python_project_files)

    @classmethod
    def install(cls) -> None:
        build_python(Path("."), "nua")


register_detector(PythonSource)
