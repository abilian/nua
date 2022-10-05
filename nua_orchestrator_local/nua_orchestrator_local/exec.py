"""Nua scripting: exec commands."""
import grp
import multiprocessing as mp
import os
import pwd
import shlex
from subprocess import run  # noqa S404

NUA = "nua"


def sudo_cmd_as_user(
    cmd: str | list,
    user: str,
    cwd: str | None = None,
    timeout=600,
    env: dict | None = None,
):
    sudo_cmd = f"sudo -nu {user} {cmd}"
    _mp_process_cmd(sudo_cmd, cwd, timeout, env)


def _mp_process_cmd(
    cmd: str | list,
    cwd: str | None = None,
    timeout: int = 600,
    env: dict | None = None,
):
    if isinstance(cmd, list):
        cmd = " ".join(cmd)
    full_env = os.environ.copy()
    if env:
        full_env.update(env)
    proc = mp.Process(target=_run_shell_cmd, args=(cmd, cwd, timeout, env))
    proc.start()
    proc.join()


def _run_shell_cmd(
    cmd: str,
    cwd: str | None = None,
    timeout: int = 600,
    env: dict | None = None,
):
    if not env:
        env = os.environ
    run(
        cmd,
        shell=True,  # noqa: S602
        timeout=timeout,
        cwd=cwd,
        executable="/bin/bash",
        env=env,
    )


def _run_cmd(
    cmd: list,
    cwd: str | None = None,
    env: dict | None = None,
    timeout: int | None = None,
):
    if not env:
        env = os.environ
    run(
        cmd,
        shell=False,
        timeout=timeout,
        cwd=cwd,
        env=env,
    )


def is_user(user: str) -> bool:
    return pwd.getpwuid(os.getuid()).pw_name == user


def _exec_as_user(cmd: str | list, user: str, env=None, timeout=None):
    if is_user(user):
        if isinstance(cmd, str):
            cmd = shlex.split(cmd)
        _run_cmd(cmd, env=env, timeout=timeout)
    elif os.getuid() == 0 or is_user(NUA):
        sudo_cmd_as_user(cmd, user, env=env, timeout=timeout)
    else:
        raise ValueError(f"Not allowed : _exec_as_user {user} as uid {os.getuid()}")


def mp_exec_as_user(cmd: str | list, user: str, env=None):
    if is_user(user):
        _mp_process_cmd(cmd, env)
    elif os.getuid() == 0 or is_user(NUA):
        sudo_cmd_as_user(cmd, user, env=env)
    else:
        raise ValueError(f"Not allowed : _mp_exec_as_user {user} as uid {os.getuid()}")


def exec_as_nua(cmd: str | list, env=None, timeout=None):
    _exec_as_user(cmd, NUA, env=env, timeout=timeout)


def mp_exec_as_nua(cmd: str | list, env=None):
    """Exec exec_as_nua() as a python external process to allow several use of
    function without mangling ENV and UID."""
    mp_exec_as_user(cmd, NUA, env)


def mp_exec_as_postgres(cmd: str | list, env=None):
    mp_exec_as_user(cmd, "postgres", env)


def exec_as_root(cmd, env=None, timeout=None):
    _exec_as_user(cmd, "root", env=env, timeout=timeout)


def _pysu_pw_uid(user, group):
    try:
        pw_record = pwd.getpwnam(user)
    except KeyError:
        pw_record = None
    if not pw_record and not group:
        raise f"Unknown user name {repr(user)}."
    if pw_record:
        uid = pw_record.pw_uid
    else:
        uid = os.getuid()
        try:
            pw_record = pwd.getpwuid(uid)
        except KeyError:
            pw_record = None

    return (pw_record, uid)


def _pysu_name_home(user, pw_record):
    if pw_record:
        home = pw_record.pw_dir
        name = pw_record.pw_name
    else:
        home = "/"
        name = user
    return name, home


def _pysu_apply_rights(name, group, uid, gid):
    if group:
        os.setgroups([gid])
    else:
        glist = os.getgrouplist(name, gid)
        os.setgroups(glist)
    os.setgid(gid)
    os.setuid(uid)


def pysu(args, user=None, group=None, env=None):
    if not env:
        env = {}
    pw_record, uid = _pysu_pw_uid(user, group)
    name, home = _pysu_name_home(user, pw_record)
    if group:
        try:
            gr_record = grp.getgrnam(group)
        except KeyError as exc:
            raise f"Unknown group name {repr(group)}." from exc
        else:
            gid = gr_record.gr_gid
    elif pw_record:
        gid = pw_record.pw_gid
    else:
        gid = uid

    _pysu_apply_rights(name, group, uid, gid)

    env["USER"] = name
    env["HOME"] = home
    env["UID"] = str(uid)
    # Starting a process without a shell (actually replacing myself):
    os.execvpe(args[0], args, env)  # noqa: S606


def ensure_env(key: str, value: str) -> None:
    """Set ENV variable is needed."""
    if os.environ.get(key) != value:
        os.environ[key] = value


def set_nua_user() -> None:
    """Ensure user is Nua and related environment.

    Will raise OSError if fails.
    """
    nua_record = pwd.getpwnam(NUA)
    if os.getuid() != nua_record.pw_uid:
        os.setgid(nua_record.pw_gid)
        os.setuid(nua_record.pw_uid)
    ensure_env("USER", NUA)
    ensure_env("HOME", nua_record.pw_dir)
    ensure_env("UID", str(nua_record.pw_uid))
    ensure_env("SHELL", str(nua_record.pw_shell))
    # os.chdir(nua_record.pw_dir)
