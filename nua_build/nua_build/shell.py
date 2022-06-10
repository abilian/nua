"""Scripting shell utils for Nua scripts."""
import os
import shutil
from pathlib import Path

# Considering possible security implications associated with the
# subprocess module.
from subprocess import run  # noqa: S404

from .panic import error, panic
from .rich_console import console


def cat(filename):
    with open(filename, encoding="utf8") as fd:
        print(fd.read())


def chown_r(path, user=None, group=None):
    for dirpath, _dirnames, filenames in os.walk(path):
        shutil.chown(dirpath, user, group)
        for filename in filenames:
            shutil.chown(os.path.join(dirpath, filename), user, group)


def echo(text: str, filename: str) -> None:
    with open(filename, "w", encoding="utf8") as fd:
        fd.write(text + "\n")


def mkdir_p(path):
    Path(path).mkdir(parents=True, exist_ok=True)


def rm_fr(path: str) -> bool:
    "Alias for rm_rf"
    return rm_rf(path)


def rm_rf(path: str) -> bool:
    """Wrapper for shutil.rmtree()"""
    if Path(path).exists():
        shutil.rmtree(path)
        return True
    return False


def sh(cmd: str, timeout=600, env=None):
    console.print(
        cmd,
        style="green",
    )
    try:
        # subprocess call with shell=True identified, security issue:
        # We do want to mimic current shell action, including all environment
        completed = run(cmd, shell=True, timeout=timeout, env=env)  # noqa: S602
        status = completed.returncode
        if status < 0:
            error(f"Child was terminated by signal {-status}", status)
        elif status > 0:
            error(f"Something went wrong (exit code: {status})", status)
    except OSError as e:
        panic(f"Execution failed: {e}")
