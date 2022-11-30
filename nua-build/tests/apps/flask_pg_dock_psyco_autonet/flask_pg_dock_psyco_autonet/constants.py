import os

# we use the resource "database", accessible as host at hostname of name:
# NUA_DATABASE_HOST

DB_HOST = os.environ.get("NUA_DATABASE_HOST")
DB_PORT = os.environ.get("DB_PORT")
POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD")
USER_DB = os.environ.get("USER_DB")
USER_NAME = os.environ.get("USER_NAME")
USER_PASSWORD = os.environ.get("USER_PASSWORD")
