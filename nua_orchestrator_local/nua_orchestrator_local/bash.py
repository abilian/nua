"""Nua comple bash environment

To be able to lanch python script with the relevant venv
"""
import multiprocessing as mp
import os
from pathlib import Path
from subprocess import run  # noqa: S404

from . import nua_env
from .exec import set_nua_user
from .panic import error


def bash_as_nua(cmd: str, cwd: str | Path | None = None, timeout=600):
    env = nua_env.as_dict()
    if not cwd:
        cwd = nua_env.nua_home()
    if not timeout:
        timeout = 600
    proc = mp.Process(target=_bash_as_nua, args=(cmd, cwd, timeout, env))
    proc.start()
    proc.join()


def _bash_as_nua(cmd, cwd, timeout, env):
    set_nua_user()
    full_env = os.environ.copy()
    full_env.update(env)
    cmd = f"source {nua_env.get_value('NUA_VENV')}/bin/activate; {cmd}"
    completed = run(
        cmd,
        shell=True,
        timeout=timeout,
        cwd=cwd,
        executable="/bin/bash",
        env=full_env,
    )  # noqa: S602
