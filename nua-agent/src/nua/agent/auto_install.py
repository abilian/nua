"""Apply automated installation detection heuristics.
"""
from pathlib import Path

from nua.lib.backports import chdir
from nua.lib.panic import info, show
from nua.lib.tool.state import verbosity

from .detectors import PythonSource, PythonWheels

AUTO_INSTALL = [
    PythonSource,
    PythonWheels,
]


def auto_install() -> bool:
    for auto_installer in AUTO_INSTALL:
        if auto_installer.detect():
            with verbosity(2):
                msg = auto_installer.info()
                show(f"{msg} detected")
            auto_installer.install()
            return True
    with verbosity(2):
        show("No automated installation detection")
    return False


def detect_and_install(directory: str | Path | None) -> bool:
    """Apply automated installation detection heuristics."""
    if directory:
        path = Path(directory).resolve()
    else:
        path = Path(".").resolve()
    with verbosity(2):
        info("Detect and install in ", path)
    with chdir(path):
        return auto_install()
