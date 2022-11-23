from nua.lib.exec import exec_as_root

setup_db()

exec_as_root("sleep 3600", env=os.environ)
