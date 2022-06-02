"""Scripting utils for Nua scripts."""
import errno
import grp
import os
import pwd
import shutil
import sys
from pathlib import Path
from subprocess import call

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
        fd.write(text)


def is_python_project():
    if Path("src/requirements.txt").exists():
        return True
    if Path("src/setup.py").exists():
        return True

    return False


# Copied from from boltons.fileutils
def mkdir_p(path):
    """Creates a directory and any parent directories that may need to be
    created along the way, without raising errors for any existing directories.

    This function mimics the behavior of the ``mkdir -p`` command
    available in Linux/BSD environments, but also works on Windows.
    """
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            return
        raise
    return


def panic(msg: str, status: int = 1):
    console.print(msg, style="bold red")
    raise SystemExit(status)


def pysu(args, user=None, group=None, env=None):
    if not env:
        env = {}
    try:
        pw = pwd.getpwnam(user)
    except KeyError:
        if group is None:
            raise f"Unknown user name {repr(user)}."
    uid = os.getuid()
    try:
        pw = pwd.getpwuid(uid)
    except KeyError:
        pw = None
    else:
        uid = pw.pw_uid

    if pw:
        home = pw.pw_dir
        name = pw.pw_name
    else:
        home = "/"
        name = user

    if group:
        try:
            gr = grp.getgrnam(group)
        except KeyError:
            raise f"Unknown group name {repr(group)}."
        else:
            gid = gr.gr_gid
    elif pw:
        gid = pw.pw_gid
    else:
        gid = uid

    if group:
        os.setgroups([gid])
    else:
        gl = os.getgrouplist(name, gid)
        os.setgroups(gl)

    os.setgid(gid)
    os.setuid(uid)
    os.environ["USER"] = name
    os.environ["HOME"] = home
    os.environ["UID"] = str(uid)
    os.execvpe(args[0], args, env)


def rm_fr(path: str) -> bool:
    "Alias for rm_rf"
    return rm_rf(path)


def rm_rf(path: str) -> bool:
    """Wrapper for shutil.rmtree()"""
    if Path(path).exists():
        shutil.rmtree(path)
        return True
    return False


def sh(cmd: str):
    console.print(cmd, style="green")
    try:
        status = call(cmd, shell=True)
        if status < 0:
            panic(f"Child was terminated by signal {-status}", status)
        elif status > 0:
            panic("Something went wrong", status)
    except OSError as e:
        panic(f"Execution failed: {e}")
