import os

from nua.lib.exec import exec_as_nua

exec_as_nua("yarn start", cwd="/nua/build/ackee", env=os.environ)
