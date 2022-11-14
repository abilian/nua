from nua.lib.common.exec import exec_as_root

cmd = "gunicorn --worker-tmp-dir /dev/shm --workers 2 -b :80 flask_two.wsgi:app"

exec_as_root(cmd)
