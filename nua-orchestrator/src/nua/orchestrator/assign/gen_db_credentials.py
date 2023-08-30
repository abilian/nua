"""Functions used to deploy new databases."""

from ..db import store
from ..utils import base20


def generate_new_user_id() -> str:
    number = store.new_user_number()
    return f"user_{base20(number)}"


def generate_new_db_id() -> str:
    number = store.new_user_number()
    return f"db_{base20(number)}"
