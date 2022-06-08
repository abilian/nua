"""Scripting utils for Nua scripts."""
import grp
import os
import pwd
import shutil
import subprocess as sp
from glob import glob
from pathlib import Path

from .rich_console import console

__all__ = """
    apt_get_install build_python cat chown_r echo error install_package_list
    is_python_project mkdir_p npm_install panic pip_install pip_list
    print_green print_magenta print_red pysu exec_as_nua exec_as_root
    replace_in rm_fr rm_rf sh
""".split()


def apt_get_install(packages: list | str) -> None:
    if isinstance(packages, str):
        packages = packages.strip().split()
    if not packages:
        return
    cmd = f"apt-get install -y {' '.join(packages)}"
    sh(cmd)


def build_python(path=None):
    # fixme: improve this
    if not path:
        path = Path()
    requirements = path / "requirements.txt"
    setup_py = path / "setup.py"
    if requirements.exists():
        sh("python -m pip install -r {str(requirements)}")
    elif setup_py.exists():
        # assuming code is in src:
        pip_install("src")


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


def install_package_list(packages):
    environ = os.environ.copy()
    environ["DEBIAN_FRONTEND"] = "noninteractive"
    cmd = f"apt-get update; apt-get install -y {' '.join(packages)}"
    sh("apt-get update", env=environ, timeout=600)
    sh(cmd, env=environ, timeout=600)
    sh("apt-get clean", env=environ, timeout=600)


def is_python_project():
    if Path("src/requirements.txt").exists():
        return True
    if Path("src/setup.py").exists():
        return True

    return False


def mkdir_p(path):
    Path(path).mkdir(parents=True, exist_ok=True)


def npm_install(package: str) -> None:
    cmd = f"/usr/bin/npm install -g {package}"
    sh(cmd)


def error(msg: str, status: int = 1):
    if not msg:
        msg = "unknown"
    if msg[-1] == ".":
        panic(f"Error: {msg.capitalize()}")
    else:
        panic(f"Error: {msg.capitalize()}.")


def panic(msg: str, status: int = 1):
    print_red(msg)
    raise SystemExit(status)


def print_green(msg: str):
    console.print(msg, style="green")


def print_magenta(msg: str):
    console.print(msg, style="magenta")


def print_red(msg: str):
    console.print(msg, style="bold red")


def pip_install(packages: list | str) -> None:
    if isinstance(packages, str):
        packages = packages.strip().split()
    if not packages:
        return
    cmd = f"python -m pip install {' '.join(packages)}"
    sh(cmd)


def pip_list():
    sh("pip list")


def exec_as_nua(cmd, env=None):
    if isinstance(cmd, str):
        cmd = cmd.split()
    full_env = os.environ.copy()
    if env:
        full_env.update(env)
    pysu(cmd, "nua", "nua", full_env)


def exec_as_root(cmd, env=None):
    if isinstance(cmd, str):
        cmd = cmd.split()
    full_env = os.environ.copy()
    if env:
        full_env.update(env)
    pysu(cmd, "root", "root", full_env)


def pysu(args, user=None, group=None, env=None):
    if not env:
        env = {}
    try:
        pw = pwd.getpwnam(user)
    except KeyError:
        if group is None:
            raise f"Unknown user name {repr(user)}."
        else:
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
    env["USER"] = name
    env["HOME"] = home
    env["UID"] = str(uid)
    os.execvpe(args[0], args, env)


def replace_in(file_pattern, searching, replace_by):
    for file_name in glob(file_pattern, recursive=True):
        path = Path(file_name)
        if not path.is_file():
            continue
        # assuming it's an utf-8 world
        with open(path, encoding="utf-8") as r:
            content = r.read()
            with open(path, mode="w", encoding="utf-8") as w:
                w.write(content.replace(searching, replace_by))


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
        completed = sp.run(cmd, shell=True, timeout=timeout, env=env)
        status = completed.returncode
        if status < 0:
            error(f"Child was terminated by signal {-status}", status)
        elif status > 0:
            error(f"Something went wrong (exit code: {status})", status)
    except OSError as e:
        panic(f"Execution failed: {e}")
