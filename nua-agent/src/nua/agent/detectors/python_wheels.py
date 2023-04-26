"""Auto install Python wheels."""
from pathlib import Path

from nua.lib.actions import pip_install

from ..auto_install import register_detector
from .base_detector import BaseDetector


class PythonWheels(BaseDetector):
    message: str = "Python wheels"
    priority: int = 110  # test order after PythonSource

    @classmethod
    def detect(cls) -> bool:
        root = Path(".").resolve()
        return bool(list(root.glob("*.whl")))

    @classmethod
    def install(cls) -> None:
        pip_install(["*.whl"], user="nua")


register_detector(PythonWheels)
