"""Nginx utils to install nginx config and adapt with app using nginx."""
import os
from time import sleep

from nua.lib.panic import Abort, debug, important, show
from nua.lib.shell import sh
from nua.lib.tool.state import verbosity

from .. import config


def _sleep_delay() -> int:
    configured_delay = config.read("host", "nginx_wait_after_restart")
    if isinstance(configured_delay, (int, float, str)):
        return int(configured_delay)
    return 1


def nginx_is_active(allow_fail: bool = False) -> bool:
    test_cmd = "systemctl -q is-active nginx && echo ok || echo ko"
    if os.geteuid() == 0:
        cmd = test_cmd
    else:
        cmd = f"sudo {test_cmd}"
    try:
        output = sh(cmd, show_cmd=False, capture_output=True)
    except Abort:
        if allow_fail:
            output = "command failed"
        else:
            raise
    return output.strip() == "ok"


def nginx_stop(allow_fail: bool = False) -> None:
    stop_cmd = "systemctl stop nginx || true"
    if os.geteuid() == 0:
        cmd = stop_cmd
    else:
        cmd = f"sudo {stop_cmd}"
    with verbosity(1):
        show(cmd)
    try:
        output = sh(cmd, show_cmd=False, capture_output=True)
    except Abort:
        if allow_fail:
            output = "command failed"
        else:
            raise
    with verbosity(3):
        debug(output)
    sleep(1)


def nginx_restart(allow_fail: bool = False) -> None:
    # assuming some recent ubuntu distribution:
    delay = _sleep_delay()
    with verbosity(1):
        important("Restart Nginx")
    restart_cmd = "systemctl restart nginx"
    if os.geteuid() == 0:
        cmd = restart_cmd
    else:
        cmd = f"sudo {restart_cmd}"
    try:
        sh(cmd, show_cmd=False)
    except Abort:
        if allow_fail:
            pass
        else:
            raise
    sleep(delay)


def nginx_reload(allow_fail: bool = False) -> None:
    # assuming some recent ubuntu distribution:
    delay = _sleep_delay()
    with verbosity(1):
        important("Reload Nginx")
    reload_cmd = "systemctl reload nginx"
    if os.geteuid() == 0:
        cmd = reload_cmd
    else:
        cmd = f"sudo {reload_cmd}"
    try:
        sh(cmd, show_cmd=False)
    except Abort:
        if allow_fail:
            pass
        else:
            raise
    sleep(delay)
