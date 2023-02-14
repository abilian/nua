"""Example adapted from:

https://www.digitalocean.com/community/tutorials/
how-to-use-a-postgresql-database-in-a-flask-application
"""

import os

from flask_sqla_sqlite_volume.app import setup_db
from nua.lib.exec import exec_as_root

setup_db()

cmd = "gunicorn --workers 2 -b :5000 flask_sqla_sqlite_volume.wsgi:app"
# exec_as_nua(cmd, env)
# We need to exec as root to be able to write files in the docker volume.
exec_as_root(cmd, env=os.environ)
