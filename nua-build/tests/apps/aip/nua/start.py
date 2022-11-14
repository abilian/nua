import os

from nua.lib.common.exec import exec_as_root
from nua.lib.common.shell import sh

sh("pip list")
sh("aip-config")
# sh("flask db upgrade")
# sh("flask db2 initdb")
sh("aip-generate-fake-data --clean")
sh("aip-bootstrap")
sh("aip-healthcheck")

port = os.environ.get("APP_PORT", 8080)
port = int(port)
cmd = f"gunicorn --bind 0.0.0.0:{port} -w 2 'app.flask.main:create_app()'"

exec_as_root(cmd)
