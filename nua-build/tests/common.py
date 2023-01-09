import os
from contextlib import AbstractContextManager
from pathlib import Path


def get_apps_root_dir(subdir: str = "") -> Path:
    """Return the path to the root of the apps directory."""
    path = Path(__file__).parent.parent.parent / "apps"
    if subdir == "":
        return path
    else:
        return path / subdir


# Copy/pasted from contextlib.py in Python 3.11
class chdir(AbstractContextManager):
    """Non thread-safe context manager to change the current working directory."""

    def __init__(self, path):
        self.path = path
        self._old_cwd = []

    def __enter__(self):
        self._old_cwd.append(os.getcwd())
        os.chdir(self.path)

    def __exit__(self, *excinfo):
        os.chdir(self._old_cwd.pop())
