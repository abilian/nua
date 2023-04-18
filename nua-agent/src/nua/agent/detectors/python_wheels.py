"""Auto install Python wheels."""
from pathlib import Path

from nua.lib.actions import pip_install

from .base_detector import BaseDetector


class PythonWheels(BaseDetector):
    message = "Python wheels"

    @classmethod
    def detect(cls) -> bool:
        root = Path(".").resolve()
        return bool(list(root.glob("*.whl")))

    @classmethod
    def install(cls) -> None:
        pip_install(["*.whl"])
