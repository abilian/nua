import os

import psycopg2

from nua.lib.exec import exec_as_nua, exec_as_root

# Nua shortcuts to manage postgres operations
from nua.runtime.postgres_manager import PostgresManager

# set in CMD_DB_HOST the actual value of the just created docker private network
CMD_DB_HOST = os.environ.get("NUA_DATABASE_HOST")
env = os.environ.copy()
env["CMD_DB_HOST"] = os.environ.get("NUA_DATABASE_HOST")

print(env)


def setup_db():
    """Find or create the required DB for app user.

    In this example The DB is on remote docker container.
    """
    manager = PostgresManager(CMD_DB_HOST, os.environ.get("CMD_DB_PORT"))
    manager.wait_for_db()
    manager.setup_db_user(
        os.environ.get("CMD_DB_DATABASE"),
        os.environ.get("CMD_DB_USERNAME"),
        os.environ.get("CMD_DB_PASSWORD"),
    )


setup_db()
exec_as_nua("node app.js", cwd="/nua/build/hedgedoc", env=env)
