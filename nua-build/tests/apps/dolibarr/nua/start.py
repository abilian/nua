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
    manager = PostgresManager(CMD_DB_HOST, os.environ.get("CMD_DB_PORT"), "", "")
    manager.setup_db_user(
        os.environ.get("CMD_DB_DATABASE"),
        os.environ.get("CMD_DB_USERNAME"),
        os.environ.get("CMD_DB_PASSWORD"),
    )


setup_db()

env = {
    "APACHE_RUN_USER": "www-data",
    "APACHE_RUN_GROUP": "www-data",
    "APACHE_PID_FILE": "/var/run/apache2/apache2.pid",
    "APACHE_RUN_DIR": "/var/run/apache2",
    "APACHE_LOCK_DIR": "/var/lock/apache2",
}

exec_as_root("/usr/sbin/apachectl -D FOREGROUND", env=env)
