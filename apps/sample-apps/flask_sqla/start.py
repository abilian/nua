from nua.lib.exec import exec_as_root

cmd = (
    "gunicorn --worker-tmp-dir /dev/shm --worker-tmp-dir /dev/shm "
    "--workers 2 -b :80 flask_sqla.wsgi:app"
)

# exec_as_nua(cmd, env)
# We need to exec as root to be able to write files in the docker volume.
exec_as_root(cmd)
