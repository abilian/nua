import os

# we use the resource "database", accessible as host at hostname of name:
# NUA_DATABASE_HOST

# DB_HOST = os.environ.get("NUA_DATABASE_HOST")
# assuming original app expect DB_HOST, not NUA_DATABASE_HOST
DB_HOST = os.environ.get("DB_HOST")

DB_PORT = os.environ.get("DB_PORT")
USER_DB = os.environ.get("USER_DB")
USER_NAME = os.environ.get("USER_NAME")
USER_PASSWORD = os.environ.get("USER_PASSWORD")
