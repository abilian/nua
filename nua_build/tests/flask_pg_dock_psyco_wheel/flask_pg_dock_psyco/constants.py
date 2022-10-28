import os

POSTGRES_DB = os.environ.get("POSTGRES_DB") or "flask_db"
POSTGRES_USER = os.environ.get("POSTGRES_USER") or "bob"
POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD") or "bob_pwd"
DB_HOST = "host.docker.internal"
DB_PORT = os.environ["NUA_RESOURCE_DATABASE_5432"]
