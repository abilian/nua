from datetime import datetime, timezone
from time import sleep, time

import psycopg2

from . import constants


def db_connection(connect_timeout=0):
    return psycopg2.connect(
        host=constants.DB_HOST,
        port=constants.DB_PORT,
        database=constants.DB_NAME,
        user=constants.DB_USERNAME,
        password=constants.DB_PASSWORD,
        connect_timeout=connect_timeout,
    )


def wait_for_db(timeout: int = 120):
    """Wait for the DB being up."""
    when = time()
    limit = when + timeout
    while time() < limit:
        while time() < when:
            sleep(0.1)
        try:
            connection = db_connection(connect_timeout=5)
            connection.close()
            now = datetime.now(timezone.utc).isoformat(" ")
            print(f"{now} - Connection ok")
            return
        except psycopg2.OperationalError:
            now = datetime.now(timezone.utc).isoformat(" ")
            print(f"{now} - Connection failed")
            when += 5.0
    raise RuntimeError(f"DB not available after {timeout} seconds.")
