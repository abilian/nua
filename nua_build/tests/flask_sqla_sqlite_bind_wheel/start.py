"""Example adapted from:
https://www.digitalocean.com/community/tutorials/how-to-use-a-postgresql-database-in-a-flask-application"""

import os

from flask_sqla_sqlite_bind.app import setup_db

from nua_build.exec import exec_as_root

setup_db()

cmd = "gunicorn --workers 2 -b :80 flask_sqla_sqlite_bind.wsgi:app"
# exec_as_nua(cmd, env)
# We need to exec as root to be able to write files in the docker volume.
exec_as_root(cmd, os.environ)
