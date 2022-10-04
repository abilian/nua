from nua_build.exec import exec_as_root

env = {}

cmd = "gunicorn --worker-tmp-dir /dev/shm --workers 2 -b :80 flask_one_poetry.wsgi:app"
exec_as_root(cmd, env)
