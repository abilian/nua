#
# Helpers
#
import subprocess

from cleez.colors import dim


def sh(cmd: str, cwd: str = "", capture=False, **kw) -> subprocess.CompletedProcess:
    """Run a shell command."""
    if not cwd:
        print(dim(f'Running "{cmd}" locally...'))
    else:
        print(dim(f'Running "{cmd}" locally in "{cwd}"...'))
    # args = shlex.split(cmd)
    opts = {
        "capture_output": capture,
        "text": True,
        "shell": True,
    }
    opts.update(kw)
    if cwd:
        opts["cwd"] = cwd
    # args_str = shlex.join(args)
    # assert args_str == cmd, (args_str, cmd)
    return subprocess.run(cmd, **opts)


def ssh(cmd: str, user="vagrant", check=True) -> subprocess.CompletedProcess:
    """Run a ssh command."""
    if user == "vagrant":
        print(dim(f'Running "{cmd}" on vagrant...'))
    else:
        print(dim(f'Running "{cmd}" on vagrant as "{user}"...'))

    # args = shlex.split(cmd)
    cmd = ["ssh", "-F", "ssh-config", f"{user}@default", cmd]  # type: ignore
    return subprocess.run(cmd, check=check)
