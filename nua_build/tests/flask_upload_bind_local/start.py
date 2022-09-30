from nua_build.exec import exec_as_root

env = {}

cmd = "gunicorn --workers 2 -b :80 flask_upload_bind_local.wsgi:app"

# exec_as_nua(cmd, env)
# We need to exec as root to be able to write files in the docker volume.
exec_as_root(cmd, env)
