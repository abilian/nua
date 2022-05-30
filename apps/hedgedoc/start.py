#!/bin/env python3

import errno
import json
import os
import pwd
import grp
import shutil
from pathlib import Path

from pprint import pprint


#
# Utils
#
def cat(filename):
    print(open(filename).read())


#
# Copied from from boltons.fileutils
def mkdir_p(path):
    """Creates a directory and any parent directories that may need to
    be created along the way, without raising errors for any existing
    directories. This function mimics the behavior of the ``mkdir -p``
    command available in Linux/BSD environments, but also works on
    Windows.
    """
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            return
        raise
    return


def chown_r(path, user=None, group=None):
    for dirpath, dirnames, filenames in os.walk(path):
        shutil.chown(dirpath, user, group)
        for filename in filenames:
            shutil.chown(os.path.join(dirpath, filename), user, group)


def pysu(args, user=None, group=None, env=None):
    if not env:
        env = {}
    try:
        pw = pwd.getpwnam(user)
    except KeyError:
        if group is None:
            raise "Unknown user name %r." % user
        else:
            uid = os.getuid()
            try:
                pw = pwd.getpwuid(uid)
            except KeyError:
                pw = None
    else:
        uid = pw.pw_uid

    if pw:
        home = pw.pw_dir
        name = pw.pw_name
    else:
        home = "/"
        name = user

    if group:
        try:
            gr = grp.getgrnam(group)
        except KeyError:
            raise "Unknown group name %r." % user
        else:
            gid = gr.gr_gid
    elif pw:
        gid = pw.pw_gid
    else:
        gid = uid

    if group:
        os.setgroups([gid])
    else:
        gl = os.getgrouplist(name, gid)
        os.setgroups(gl)

    os.setgid(gid)
    os.setuid(uid)
    os.environ["USER"] = name
    os.environ["HOME"] = home
    os.environ["UID"] = str(uid)
    os.execvpe(args[0], args, env)


#
#
#
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
    "CMD_DOMAIN": NUA_APP_DOMAIN,
    "HD_DOMAIN": NUA_APP_DOMAIN,
    "HD_DB_URL": NUA_POSTGRESQL_URL,
    "HD_PROTOCOL_USESSL": "true",
    "HD_PORT": "3000",
    "HD_TMP_PATH": "/tmp/hedgedoc",
    "HD_USECDN": "false",
    "NODE_ENV": "production",
}


# run
pysu(["node", "app.js"], "nua", "nua", ENV)
