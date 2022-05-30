#
# Utils (complements to shutils and similar libs)
#
import errno
import os
import shutil
import sys
from pathlib import Path

import rich.console

console = rich.console.Console()


def sh(cmd: str):
    console.print(cmd, style="green")
    status = os.system(cmd)
    if status != 0:
        panic("Something went wrong", status)


def panic(msg: str, status: int = 1):
    console.print(msg, style="bold red")
    sys.exit(status)


# Copied from from boltons.fileutils
def mkdir_p(path):
    """Creates a directory and any parent directories that may need to
    be created along the way, without raising errors for any existing
    directories. This function mimics the behavior of the ``mkdir -p``
    command available in Linux/BSD environments, but also works on
    Windows.
    """
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            return
        raise
    return


def rm_rf(path: str):
    if Path(path).exists():
        shutil.rmtree(path)
