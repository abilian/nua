"""Nginx utils to install nginx config and adapt with app using nginx."""
import os
from time import sleep

from nua.lib.panic import debug, important, show
from nua.lib.shell import sh
from nua.lib.tool.state import verbosity

from .. import config


def nginx_is_active() -> bool:
    test_cmd = "systemctl -q is-active nginx && echo ok || echo ko"
    if os.geteuid() == 0:
        cmd = test_cmd
    else:
        cmd = f"sudo {test_cmd}"
    output = sh(cmd, show_cmd=False, capture_output=True)
    return output.strip() == "ok"


def nginx_stop():
    stop_cmd = "systemctl stop nginx || true"
    if os.geteuid() == 0:
        cmd = stop_cmd
    else:
        cmd = f"sudo {stop_cmd}"
    with verbosity(2):
        show(cmd)
    output = sh(cmd, show_cmd=False, capture_output=True)
    with verbosity(3):
        debug(output)
    sleep(1)


def nginx_restart():
    # assuming some recent ubuntu distribution:
    delay = config.read("host", "nginx_wait_after_restart") or 1
    with verbosity(2):
        important("Restart Nginx")
    cmd = "systemctl restart nginx"
    if os.geteuid() == 0:
        sh(cmd, show_cmd=False)
    else:
        sh(f"sudo {cmd}", show_cmd=False)
    sleep(delay)


def nginx_reload():
    # assuming some recent ubuntu distribution:
    if not nginx_is_active():
        return nginx_restart()
    delay = config.read("host", "nginx_wait_after_restart") or 1
    with verbosity(2):
        important("Reload Nginx")
    cmd = "systemctl reload nginx"
    if os.geteuid() == 0:
        sh(cmd, show_cmd=False)
    else:
        sh(f"sudo {cmd}", show_cmd=False)
    sleep(delay)
