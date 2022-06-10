"""Nua scripting: exec commands."""
import grp
import os
import pwd


def exec_as_nua(cmd, env=None):
    if isinstance(cmd, str):
        cmd = cmd.split()
    full_env = os.environ.copy()
    if env:
        full_env.update(env)
    pysu(cmd, "nua", "nua", full_env)


def exec_as_root(cmd, env=None):
    if isinstance(cmd, str):
        cmd = cmd.split()
    full_env = os.environ.copy()
    if env:
        full_env.update(env)
    pysu(cmd, "root", "root", full_env)


def _pysu_pw_uid(user, group):
    try:
        pw_record = pwd.getpwnam(user)
    except KeyError:
        pw_record = None
    if not pw_record and not group:
        raise f"Unknown user name {repr(user)}."
    if pw_record:
        uid = pw_record.pw_uid
    else:
        uid = os.getuid()
        try:
            pw_record = pwd.getpwuid(uid)
        except KeyError:
            pw_record = None

    return (pw_record, uid)


def _pysu_name_home(user, pw_record):
    if pw_record:
        home = pw_record.pw_dir
        name = pw_record.pw_name
    else:
        home = "/"
        name = user
    return name, home


def _pysu_apply_rights(name, group, uid, gid):
    if group:
        os.setgroups([gid])
    else:
        glist = os.getgrouplist(name, gid)
        os.setgroups(glist)
    os.setgid(gid)
    os.setuid(uid)


def pysu(args, user=None, group=None, env=None):
    if not env:
        env = {}
    pw_record, uid = _pysu_pw_uid(user, group)
    name, home = _pysu_name_home(user, pw_record)
    if group:
        try:
            gr_record = grp.getgrnam(group)
        except KeyError:
            raise f"Unknown group name {repr(group)}."
        else:
            gid = gr_record.gr_gid
    elif pw_record:
        gid = pw_record.pw_gid
    else:
        gid = uid

    _pysu_apply_rights(name, group, uid, gid)

    env["USER"] = name
    env["HOME"] = home
    env["UID"] = str(uid)
    # Starting a process without a shell (actually replacing myself):
    os.execvpe(args[0], args, env)  # noqa: S606
