import os

DB_NAME = os.environ.get("DB_NAME") or "flask_db"
DB_USER = os.environ.get("DB_USER") or "bob"
DB_USER_PWD = os.environ.get("DB_USER_PWD") or "bob_pwd"
DB_HOST = os.environ.get("DB_HOST")
# DB_HOST = "host.docker.internal"
