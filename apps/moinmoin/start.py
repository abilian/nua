#!/bin/env python3

import errno
import grp
import json
import os
import pwd
import shutil
from pathlib import Path
from pprint import pprint

from nua_build.scripting import *


#
# Main
#
def main():
    return

    mkdir_p("/app/data/uploads")
    mkdir_p("/tmp/hedgedoc")
    mkdir_p("/run/hedgedoc")

    chown_r("/app/data", "nua")
    chown_r("/tmp/hedgedoc", "nua")
    chown_r("/run/hedgedoc", "nua")

    #
    # Set up config on first run
    #
    CONFIG_JSON = "/app/data/config.json"

    if not Path(CONFIG_JSON).exists():
        shutil.copy("/app/pkg/config.json.j2", CONFIG_JSON)

    cat(CONFIG_JSON)

    config_json = json.load(open("/app/data/config.json"))
    pprint(config_json)

    if not "sessionSecret" in config_json["production"]:
        config_json["production"]["sessionSecret"] = "1234"  # TODO

    with open(CONFIG_JSON, "w") as fd:
        json.dump(config_json, fd)

    cat(CONFIG_JSON)

    #
    # Environment
    #
    NUA_APP_DOMAIN = "test.abilian.com"
    NUA_POSTGRESQL_URL = "toto"

    ENV = {
        "USE_POSTGRESQL": "1",
        "DJANGO_SETTINGS_MODULE": "config.docker_config",
    }

    # run
    pysu(
        ["python", "pytition/manage.py", "runserver", "0.0.0.0:8000"], "nua", "nua", ENV
    )


if __name__ == "__main__":
    main()
