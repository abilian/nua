import os

from flask_mariadb_docker_wheel.init_db import init_db
from nua.lib.exec import exec_as_root

init_db()

cmd = (
    "gunicorn --worker-tmp-dir /dev/shm --workers 2 -b :80 "
    "flask_mariadb_docker_wheel.wsgi:app"
)
# exec_as_nua(cmd, env)
# We need to exec as root to be able to write files in the docker volume.
exec_as_root(cmd, env=os.environ)
