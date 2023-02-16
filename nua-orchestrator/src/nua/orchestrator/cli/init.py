import os

import typer
from nua.lib.actions import check_python_version
from nua.lib.console import print_red
from nua.lib.exec import is_current_user, set_nua_user
from nua.lib.panic import abort, vprint
from nua.lib.tool.state import verbosity

from ..nua_db_setup import setup_nua_db
from ..register_plugins import register_plugins

is_initialized = False


def initialization():
    global is_initialized

    if not check_python_version():
        abort("Python 3.10+ is required for Nua orchestrator.")
    if os.getuid() == 0 or is_current_user("nua"):
        set_nua_user()
    else:
        print_red("Warning: Nua orchestrator must be run as 'root' or 'nua'.")
        raise typer.Exit(1)
    if is_initialized:
        with verbosity(3):
            vprint("already initialized")
        return

    setup_nua_db()
    register_plugins()
    is_initialized = True
