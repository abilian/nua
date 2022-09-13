"""Scripting shell utils for Nua scripts."""
import grp
import os
import pwd
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


def chown_r(path, user: str, group=None):
    record = pwd.getpwnam(user)
    uid = record.pw_uid
    if group:
        gr_record = grp.getgrnam(group)
        gid = gr_record.gr_gid
    else:
        gid = record.pw_gid
    for dirpath, _dirnames, filenames in os.walk(path):
        os.chown(dirpath, uid, gid, follow_symlinks=False)
        for filename in filenames:
            os.chown(os.path.join(dirpath, filename), uid, gid, follow_symlinks=False)


def echo(text: str, filename: str) -> None:
    with open(filename, "w", encoding="utf8") as fd:
        fd.write(text + "\n")


def mkdir_p(path):
    Path(path).mkdir(parents=True, exist_ok=True)


def rm_fr(path: str | Path) -> bool:
    """Alias for rm_rf."""
    return rm_rf(path)


def rm_rf(path: str | Path) -> bool:
    """Wrapper for shutil.rmtree()"""
    if Path(path).exists():
        shutil.rmtree(path)
        return True
    return False


def _base_sh(cmd: str, timeout: int, env: dict | None, capture_output: bool):
    if capture_output:
        return run(
            cmd,
            shell=True,  # noqa: S602
            timeout=timeout,
            env=env,
            capture_output=True,
            encoding="utf8",
            text=True,
        )
    else:
        return run(cmd, shell=True, timeout=timeout, env=env)  # noqa: S602


def sh(
    cmd: str,
    timeout: int = 600,
    env: dict | None = None,
    show_cmd: bool = True,
    capture_output: bool = False,
) -> str:
    if show_cmd:
        console.print(
            cmd,
            style="green",
        )
    try:
        # subprocess call with shell=True identified, security issue:
        # We do want to mimic current shell action, including all environment
        completed = _base_sh(cmd, timeout, env, capture_output)
        status = completed.returncode
        if status < 0:
            error(f"Child was terminated by signal {-status}", status)
        elif status > 0:
            error(f"Something went wrong (exit code: {status})", status)
    except OSError as e:
        panic(f"Execution failed: {e}")
    if capture_output:
        return completed.stdout
    else:
        return ""


def user_exists(user: str) -> bool:
    try:
        pwd.getpwnam(user)
        return True
    except KeyError:
        return False
