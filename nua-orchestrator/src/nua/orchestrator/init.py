import os

from nua.lib.actions import check_python_version
from nua.lib.exec import is_current_user, set_nua_user
from nua.lib.panic import Abort, vprint
from nua.lib.tool.state import verbosity

from .nua_db_setup import setup_nua_db

is_initialized = False


def initialization():
    global is_initialized

    if not check_python_version():
        raise Abort("Python 3.10+ is required for Nua orchestrator.")

    if os.getuid() != 0 and not is_current_user("nua"):
        raise Abort("Error: Nua orchestrator must be run as 'root' or 'nua'.")

    set_nua_user()

    if is_initialized:
        with verbosity(3):
            vprint("already initialized")
        return

    setup_nua_db()
    is_initialized = True
