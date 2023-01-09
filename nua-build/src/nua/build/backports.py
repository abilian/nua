import os
from contextlib import AbstractContextManager


# Copy/pasted from contextlib.py in Python 3.11
class chdir(AbstractContextManager):  # noqa: N801
    """Non thread-safe context manager to change the current working
    directory."""

    def __init__(self, path):
        self.path = path
        self._old_cwd = []

    def __enter__(self):
        self._old_cwd.append(os.getcwd())
        os.chdir(self.path)

    def __exit__(self, *excinfo):
        os.chdir(self._old_cwd.pop())
