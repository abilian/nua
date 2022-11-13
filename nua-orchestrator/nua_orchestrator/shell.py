"""Scripting shell utils for Nua scripts."""
import pwd
import shutil
from pathlib import Path

# Considering possible security implications associated with the
# subprocess module.
from subprocess import run  # noqa: S404

from .panic import error
from .rich_console import console


def cat(filename: str | Path):
    with open(filename, encoding="utf8") as fd:
        print(fd.read())


def chown_r(path: str | Path, user: str, group: str | None = None):
    """Apply recursively chown with str arguments.

    example:
        chown_r(document_root, "www-data", "www-data")
    """
    root = Path(path)
    if root.is_dir():
        for subpath in root.rglob(""):
            shutil.chown(subpath, user, group or user)
    else:
        shutil.chown(root, user, group or user)


def _dir_chmod_r(root: Path, file_mode: int, dir_mode: int):
    for subpath in root.rglob(""):
        if subpath.is_dir():
            subpath.chmod(dir_mode)
        else:
            subpath.chmod(file_mode)


def chmod_r(path: str | Path, file_mode: int, dir_mode: int | None = None):
    """Apply recursively chmod with int arguments.

    example:
        chmod_r(document_root, 0o644, 0o755)
    """
    root = Path(path)
    if dir_mode is None:
        dir_mode = file_mode
    if root.is_dir():
        _dir_chmod_r(root, file_mode, dir_mode)
    else:
        root.chmod(file_mode)


def echo(text: str, filename: str | Path) -> None:
    Path(filename).write_text(text + "\n", encoding="utf8")


def mkdir_p(path: str | Path):
    Path(path).mkdir(parents=True, exist_ok=True)


def rm_fr(path: str | Path) -> bool:
    """Alias for rm_rf."""
    return rm_rf(path)


def rm_rf(path: str | Path) -> bool:
    """Wrapper for shutil.rmtree()."""
    if Path(path).exists():
        shutil.rmtree(path)
        return True
    return False


def _base_sh(cmd: str, timeout: int, env: dict | None, capture_output: bool):
    if capture_output:
        return run(
            cmd,
            shell=True,  # noqa: S602
            executable="/bin/bash",
            timeout=timeout,
            env=env,
            capture_output=True,
            encoding="utf8",
            text=True,
        )
    else:
        return run(
            cmd,
            shell=True,  # noqa: S602
            executable="/bin/bash",
            timeout=timeout,
            env=env,
        )


def sh(
    cmd: str,
    timeout: int | None = 600,
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
            msg = (
                f"Child was terminated by signal {-status},\n"
                f"shell command was: '{cmd}'\n"
            )
            error(msg, status)
        elif status > 0:
            msg = (
                f"Something went wrong (exit code: {status}), \n"
                f"shell command was: '{cmd}'\n"
            )
            error(msg, status)
    except OSError as e:
        error(f"Execution failed: {e}\nshell command was: '{cmd}'\n")
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
