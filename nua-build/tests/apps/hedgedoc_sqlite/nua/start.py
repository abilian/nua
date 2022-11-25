import os

from nua.lib.exec import exec_as_nua

exec_as_nua("node app.js", cwd="/nua/build/hedgedoc", env=os.environ)
