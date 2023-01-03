import os

from nua.lib.exec import exec_as_nua
# Nua shortcuts to manage postgres operations
from nua.runtime.db.postgres_manager import PostgresManager


def setup_db():
    """Find or create the required DB for app user.

    In this example The DB is on remote docker container.
    """
    manager = PostgresManager(
        host=os.environ.get("CMD_DB_HOST"), port=os.environ.get("CMD_DB_PORT")
    )
    manager.wait_for_db()
    manager.setup_db_user(
        os.environ.get("CMD_DB_DATABASE"),
        os.environ.get("CMD_DB_USERNAME"),
        os.environ.get("CMD_DB_PASSWORD"),
    )


setup_db()
exec_as_nua("node app.js", cwd="/nua/build/hedgedoc", env=os.environ)
