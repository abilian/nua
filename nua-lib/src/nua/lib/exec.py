"""Nua scripting: exec commands."""
import multiprocessing as mp
import os
import pwd
import shlex
from subprocess import DEVNULL, run  # noqa S404

NUA = "nua"


def sudo_cmd_as_user(  # noqa CFQ002
    cmd: str | list,
    user: str,
    *,
    cwd: str | None = None,
    timeout: int | None = None,
    env: dict | None = None,
    show_cmd: bool = True,
    set_home=True,
):
    if isinstance(cmd, list):
        cmd = " ".join(cmd)
    sudo_cmd = f"sudo -nu {user} {cmd}"
    if show_cmd:
        print(cmd)
    if set_home:
        if not env:
            env = {}
        env["HOME"] = pwd.getpwnam(user).pw_dir
    _mp_process_cmd(sudo_cmd, cwd=cwd, timeout=timeout, env=env, show_cmd=show_cmd)


def _mp_process_cmd(
    cmd: str | list,
    cwd: str | None = None,
    timeout: int | None = None,
    env: dict | None = None,
    show_cmd: bool = True,
):
    proc = mp.Process(target=_run_shell_cmd, args=(cmd, cwd, timeout, env, show_cmd))
    proc.start()
    proc.join()


def _run_shell_cmd(
    cmd: str | list,
    cwd: str | None = None,
    timeout: int | None = None,
    env: dict | None = None,
    show_cmd: bool = True,
):
    _env = dict(os.environ)
    if env:
        _env.update(env)
    if show_cmd:
        stdout = None
    else:
        stdout = DEVNULL
    run(
        cmd,
        shell=True,  # noqa: S602
        timeout=timeout,
        cwd=cwd,
        executable="/bin/bash",
        env=_env,
        stdout=stdout,
    )


def _run_cmd(
    cmd: str | list,
    cwd: str | None = None,
    timeout: int | None = None,
    env: dict | None = None,
    show_cmd: bool = True,
):
    if isinstance(cmd, str):
        cmd = shlex.split(cmd)
    if env is None:
        _env = dict(os.environ)
    else:
        _env = env
    if show_cmd:
        stdout = None
    else:
        stdout = DEVNULL
    run(
        cmd,
        shell=False,  # noqa S603
        timeout=timeout,
        cwd=cwd,
        env=_env,
        stdout=stdout,
    )


def is_current_user(user: str) -> bool:
    return pwd.getpwuid(os.getuid()).pw_name == user


def _exec_as_user(
    cmd: str | list,
    user: str,
    cwd: str | None = None,
    timeout: int | None = None,
    env: dict | None = None,
    show_cmd: bool = True,
):
    if isinstance(cmd, str):
        cmd = [cmd]
    if is_current_user(user):
        for command in cmd:
            _run_cmd(command, timeout=timeout, env=env, show_cmd=show_cmd)
    elif os.getuid() == 0 or is_current_user(NUA):
        for command in cmd:
            sudo_cmd_as_user(
                command, user, cwd=cwd, timeout=timeout, env=env, show_cmd=show_cmd
            )
    else:
        raise ValueError(f"Not allowed : _exec_as_user {user} as uid {os.getuid()}")


def mp_exec_as_user(
    cmd: str | list,
    user: str,
    *,
    cwd: str | None = None,
    env: dict | None = None,
    timeout: int | None = None,
    show_cmd: bool = True,
):
    if is_current_user(user):
        _mp_process_cmd(cmd, timeout=timeout, env=env, show_cmd=show_cmd)
    elif os.getuid() == 0 or is_current_user(NUA):
        sudo_cmd_as_user(
            cmd, user, cwd=cwd, timeout=timeout, env=env, show_cmd=show_cmd
        )
    else:
        raise ValueError(f"Not allowed : mp_exec_as_user '{user}' as uid {os.getuid()}")


def exec_as_nua(
    cmd: str | list,
    cwd: str | None = None,
    env: dict | None = None,
    timeout: int | None = None,
):
    """Exec command or list of commands as user nua."""
    _exec_as_user(cmd, NUA, cwd=cwd, timeout=timeout, env=env)


def mp_exec_as_nua(
    cmd: str | list,
    cwd: str | None = None,
    env: dict | None = None,
    timeout: int | None = None,
):
    """Exec exec_as_nua() as a python external process to allow several use of
    function without mangling ENV and UID."""
    mp_exec_as_user(cmd, NUA, cwd=cwd, timeout=timeout, env=env)


def exec_as_root_daemon(
    cmd: str,
    env: dict | None = None,
) -> mp.Process:
    """Exec a subprocess daemon as root()."""
    if os.getuid() != 0:
        if is_current_user(NUA):
            cmd = "sudo " + cmd
        else:
            raise ValueError(f"Not allowed : exec_as_root_daemon as uid {os.getuid()}")
    args = tuple(shlex.split(cmd))
    if not env:
        _env = dict(os.environ)
    else:
        _env = env
    proc = mp.Process(target=_run_cmd, args=args, kwargs={"env": _env}, daemon=True)
    proc.start()
    return proc


def mp_exec_as_postgres(
    cmd: str | list,
    cwd: str | None = None,
    env: dict | None = None,
    timeout: int | None = None,
    show_cmd: bool = True,
):
    """Exec as user 'postgres' in a python external process to allow several
    use of function without mangling ENV and UID."""
    mp_exec_as_user(
        cmd, "postgres", cwd=cwd, timeout=timeout, env=env, show_cmd=show_cmd
    )


def exec_as_root(
    cmd: str | list,
    cwd: str | None = None,
    env: dict | None = None,
    timeout: int | None = None,
    show_cmd: bool = True,
):
    """Exec command or list of commands as user root."""
    _exec_as_user(cmd, "root", cwd=cwd, timeout=timeout, env=env, show_cmd=show_cmd)


def set_nua_user() -> None:
    """Ensure user is Nua and related environment.

    Will raise OSError if fails.
    """
    nua_record = pwd.getpwnam(NUA)
    if os.getuid() != nua_record.pw_uid:
        os.setgid(nua_record.pw_gid)
        os.setuid(nua_record.pw_uid)

    os.environ["USER"] = NUA
    os.environ["HOME"] = nua_record.pw_dir
    os.environ["UID"] = str(nua_record.pw_uid)
    os.environ["SHELL"] = str(nua_record.pw_shell)
    # os.chdir(nua_record.pw_dir)
