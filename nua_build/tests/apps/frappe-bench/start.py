"""at start, just test intalled versions"""

import os

# from nua_build import mariadb_utils as mdb  # Nua shortcuts to manage mariadb
from nua_build.exec import exec_as_nua

os.environ.update(
    {
        "SHELL": "/bin/bash",
        "HOME": "/nua",
        "NVM_DIR": "/nua/.nvm",
        "BENCH_DEVELOPER": "1",
        "PATH": "/nua/venv/bin:/nua/.local/bin:/nua/.nvm/versions/node/v16.18.0/bin/:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
    }
)

env = os.environ
exec_as_nua("node --version", env=env)
exec_as_nua("npm --version", env=env)
exec_as_nua("yarn --version", env=env)
exec_as_nua("bench --version", env=env)
