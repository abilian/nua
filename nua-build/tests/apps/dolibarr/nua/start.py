import os

import psycopg2
from nua.lib.exec import exec_as_nua, exec_as_root

# Nua shortcuts to manage postgres operations
from nua.runtime.postgres_manager import PostgresManager

# set in CMD_DB_HOST the actual value of the just created docker private network
# This laybe not needed now (see [instance.db_host])
# DOLI_DB_HOST = os.environ.get("NUA_DATABASE_HOST")
# env = os.environ.copy()
# env["DOLI_DB_HOST"] = os.environ.get("NUA_DATABASE_HOST")

print(env)


def setup_db():
    """Find or create the required DB for app user.

    In this example The DB is on remote docker container.
    """
    manager = PostgresManager(
        host=DOLI_DB_HOST, port=os.environ.get("DOLI_DB_HOST_PORT")
    )
    print("pass:", manager.password)
    manager.setup_db_user(
        os.environ.get("DOLI_DB_NAME"),
        os.environ.get("DOLI_DB_USER"),
        os.environ.get("DOLI_DB_PASSWORD"),
    )


setup_db()
print("setup_db done")

exec_as_root("/bin/bash /nua/build/nua/entrypoint.sh")

env = {
    "APACHE_RUN_USER": "www-data",
    "APACHE_RUN_GROUP": "www-data",
    "APACHE_PID_FILE": "/var/run/apache2/apache2.pid",
    "APACHE_RUN_DIR": "/var/run/apache2",
    "APACHE_LOCK_DIR": "/var/lock/apache2",
}

exec_as_root("/usr/sbin/apachectl -D FOREGROUND", env=env)
