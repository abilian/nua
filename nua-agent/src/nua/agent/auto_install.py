"""Apply automated installation detection heuristics.
"""
from importlib import import_module
from importlib import resources as rso
from operator import attrgetter
from pathlib import Path
from typing import Any

from nua.lib.backports import chdir
from nua.lib.panic import info, show
from nua.lib.tool.state import verbosity

from .detectors.base_detector import BaseDetector

DETECTORS_DIRS = ("nua.agent.detectors",)
detector_classes: set[BaseDetector] = set()


def detect_and_install(directory: str | Path | None) -> bool:
    """Apply automated installation detection heuristics."""
    if not detector_classes:
        register_detectors()
    if directory:
        path = Path(directory).resolve()
    else:
        path = Path(".").resolve()
    with verbosity(2):
        info("Detect and install in ", path)
    with chdir(path):
        return auto_install()


def auto_install() -> bool:
    for auto_installer in sorted(detector_classes, key=attrgetter("priority")):
        if auto_installer.detect():
            with verbosity(2):
                msg = auto_installer.info()
                show(f"{msg} detected")
            auto_installer.install_with_build_packages()
            return True
    with verbosity(2):
        show("No automated installation found")
    return False


def register_detectors():
    for dir in DETECTORS_DIRS:
        for file in rso.files(dir).iterdir():
            path = Path(str(file))
            if path.suffix != ".py" or path.stem.startswith("_"):
                continue
            module_path = f"nua.agent.detectors.{path.stem}"
            import_module(module_path)


def register_detector(cls: Any):
    detector_classes.add(cls)
