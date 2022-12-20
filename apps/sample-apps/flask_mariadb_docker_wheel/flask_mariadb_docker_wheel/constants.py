import os

# we use the resource "mariadb", accessible as host at hostname of name:
# NUA_MARIADB_HOST

DB_HOST = os.environ.get("NUA_MARIADB_HOST")
DB_PORT = "3306"
MARIADB_ROOT_PASSWORD = os.environ.get("MARIADB_ROOT_PASSWORD")
USER_DB = os.environ.get("USER_DB")
USER_NAME = os.environ.get("USER_NAME")
USER_PASSWORD = os.environ.get("USER_PASSWORD")
