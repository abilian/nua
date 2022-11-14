from nua.lib.common.exec import exec_as_nua

cmd = "gunicorn --worker-tmp-dir /dev/shm --workers 2 -b :80 flask_sub_folder.wsgi:app"

exec_as_nua(cmd)
