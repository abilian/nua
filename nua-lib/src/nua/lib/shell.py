"""Scripting shell utils for Nua scripts."""
import pwd
import shutil
from pathlib import Path
from subprocess import CompletedProcess, run  # noqa: S404

from .panic import Abort, show


def cat(filename: str | Path):
    with open(filename, encoding="utf8") as fd:
        print(fd.read())


def chown_r(path: str | Path, user: str, group: str | None = None):
    """Apply recursively chown with str arguments.

    Similar to `chown -R`.

    example:
        chown_r(document_root, "www-data", "www-data")
    """
    root = Path(path).absolute()
    # broken on symlinks ?
    # for item in root.rglob("*"):
    #     print(item, item.is_file())
    #     shutil.chown(item, user, group or user)
    # shutil.chown(root, user, group or user)
    sh(f"chown -R {user}:{group or user} {root}", show_cmd=False)


def chmod_r(path: str | Path, file_mode: int, dir_mode: int | None = None):
    """Apply recursively chmod with int arguments.

    Similar to `chmod -R` but with int arguments (usually expressed as octal numbers).

    example:
        chmod_r(document_root, 0o644, 0o755)
    """
    root = Path(path)
    if dir_mode is None:
        dir_mode = file_mode
    for item in root.rglob("*"):
        if item.is_dir():
            item.chmod(dir_mode)
        else:
            item.chmod(file_mode)
    if root.is_dir():
        root.chmod(dir_mode)
    else:
        root.chmod(file_mode)


# XXX: not used
def _dir_chmod_r(root: Path, file_mode: int, dir_mode: int):
    for subpath in root.rglob(""):
        if subpath.is_dir():
            subpath.chmod(dir_mode)
        else:
            subpath.chmod(file_mode)


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


def _base_sh(
    cmd: str,
    timeout: int | None,
    env: dict | None,
    capture_output: bool,
    cwd: str | Path | None,
) -> CompletedProcess:
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
            cwd=cwd,
        )
    else:
        return run(
            cmd,
            shell=True,  # noqa: S602
            executable="/bin/bash",
            timeout=timeout,
            env=env,
            cwd=cwd,
        )


def sh(
    cmd: str,
    timeout: int | None = 600,
    env: dict | None = None,
    show_cmd: bool = True,
    capture_output: bool = False,
    cwd: str | Path | None = None,
) -> str | bytes:
    # XXX: can/should it really return bytes?
    """Run a shell command."""
    if show_cmd:
        show(cmd)

    try:
        # subprocess call with shell=True identified, security issue:
        # We do want to mimic current shell action, including all environment
        completed = _base_sh(cmd, timeout, env, capture_output, cwd)
        status = completed.returncode
        if status < 0:
            msg = (
                f"Child was terminated by signal {-status},\n"
                f"shell command was: '{cmd}'"
            )
            raise Abort(msg, status)
        elif status > 0:
            msg = (
                f"Something went wrong (exit code: {status}), \n"
                f"shell command was: '{cmd}'\n"
                f"{completed.stdout}\n"
                f"{completed.stderr}"
            )
            raise Abort(msg, status)
    except OSError as e:
        raise Abort(f"Execution failed: {e}\nshell command was: '{cmd}'")

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
