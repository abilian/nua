"""Auto install Nodejs/Yarn."""
from pathlib import Path

from nua.lib.shell import sh

from ..auto_install import register_detector
from .base_detector import BaseDetector


class NodejsYarn(BaseDetector):
    message: str = "Nodejs yarn"
    priority: int = 100

    @classmethod
    def detect(cls) -> bool:
        root = Path(".").resolve()
        return (root / "yarn.lock").exists()

    @classmethod
    def install(cls) -> None:
        sh("yarn install")


register_detector(NodejsYarn)
