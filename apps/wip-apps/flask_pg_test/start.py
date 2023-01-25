"""Example adapted from:

https://www.digitalocean.com/community/tutorials/how-to-use-a-postgresql-database-in-a-flask-application
"""

import os

from flask_pg_test.init_db import init_db
from nua.lib.exec import exec_as_nua

init_db()

cmd = "gunicorn --worker-tmp-dir /dev/shm --workers 2 -b :5000 flask_pg_test.wsgi:app"
# exec_as_nua(cmd, env)
# We need to exec as root to be able to write files in the docker volume.
exec_as_nua(cmd, env=os.environ)
