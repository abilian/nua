from nua_build.exec import exec_as_nua

env = {}

cmd = "gunicorn --workers 2 -b :80 flask_sub_folder.wsgi:app"

exec_as_nua(cmd, env)
