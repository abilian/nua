import os

from nua.lib.exec import exec_as_nua

print("--------------------------")
print(os.environ)
print("--------------------------")
exec_as_nua("yarn start", cwd="/nua/build/ackee", env=os.environ)
