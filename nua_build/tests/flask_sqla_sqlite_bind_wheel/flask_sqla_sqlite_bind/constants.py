import os

DB_FOLDER = os.environ.get("DB_FOLDER") or "/nua/app/dbs"
DB_NAME = os.environ.get("DB_NAME") or "default_test.db"
