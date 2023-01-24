"""Functions used to deploy new databases."""
# from pathlib import Path
#
# from nua.lib.panic import abort, info, warning
# from nua.lib.tool.state import verbosity

from .db import store
from .nua_db_setup import setup_nua_db
from .utils import base20


def generate_new_user_id() -> int:
    setup_nua_db()
    number = store.new_user_number()
    return f"user_{base20(number)}"
