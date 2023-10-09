from pathlib import Path

from .db_utils.mariadb_utils import NUA_MARIADB_PWD_FILE
from .db_utils.postgres_utils import NUA_PG_PWD_FILE


def secrets_dict(key_list: list) -> dict:
    result = {}
    for key in key_list:
        val = read_secret(key)
        if val is not None:
            result[key] = val
    return result


def read_secret(key: str) -> str | None:
    if key == "POSTGRES_PASSWORD":
        return _postgres_pwd()
    if key in {"MARIADB_ROOT_PASSWORD", "MYSQL_ROOT_PASSWORD"}:
        return _mariadb_pwd()
    return None


def _postgres_pwd() -> str:
    """Return the 'postgres' user DB password.

    Read the password from local file.

    Assuming this function can only be used *after* password was
    generated (or it's a bug).
    """
    # pwd = os.environ.get("NUA_POSTGRES_PASSWORD")
    # if pwd:
    #     return pwd
    file_path = Path("~nua").expanduser() / NUA_PG_PWD_FILE
    return file_path.read_text(encoding="utf8").strip()


def _mariadb_pwd() -> str:
    """Return the 'root' user DB password of mariadb.

    Read the password from local file.

    Assuming this function can only be used *after* password was
    generated (or it's a bug).
    """
    # pwd = os.environ.get("NUA_MARIADB_PASSWORD")
    # if pwd:
    #     return pwd
    file_path = Path("~nua").expanduser() / NUA_MARIADB_PWD_FILE
    return file_path.read_text(encoding="utf8").strip()
