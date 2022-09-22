from nua_build.exec import exec_as_root

env = {}

cmd = "gunicorn --workers 2 -b :80 flask_two.wsgi:app"

exec_as_root(cmd, env)
