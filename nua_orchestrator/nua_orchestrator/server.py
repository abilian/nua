#!/usr/bin/env python
"""Nua main server.

Main server only duty is to launch and manage sub servers:
  - sentinel server, enforcing the .pid file security.
  - zmq RPC server, in charge of CLI requests
  - in the future: other services
"""
import atexit
import multiprocessing as mp
import os
import sys
from pathlib import Path
from time import sleep

import psutil
import toml

from .nua_db import create_base
from .server_utils.forker import forker
from .server_utils.mini_log import log, log_me, log_sentinel
from .zmq_rpc_server import start_zmq_rpc_server

CONFIG = toml.load(Path(__file__).parent.resolve() / "params.toml")
PID_FILE = Path(CONFIG["server"]["pid_file"])
EXIT_FLAG = Path(CONFIG["server"]["exit_flag"])
# NOTE: /tmp is not ideal, but /run would require some privileges: see later.
# see later for log module implementation
os.environ["NUA_LOG_FILE"] = CONFIG["server"].get("log_file", "")


def unlink_pid_file():
    """Unlink the server pid file, no fail on error."""
    if PID_FILE.exists():
        try:
            PID_FILE.unlink(missing_ok=True)
        except OSError:
            pass


def touch_exit_flag():
    """Create a temporary flag file, to secure server stop/start ordering."""
    if EXIT_FLAG.exists():
        return
    EXIT_FLAG.parent.mkdir(exist_ok=True)

    with open(EXIT_FLAG, "w", encoding="utf8") as f:
        try:
            f.write("\n")
        except OSError:
            pass


def unlink_exit_flag():
    """Unlink the EXIT_FLAG, no fail on error."""
    try:
        EXIT_FLAG.unlink(missing_ok=True)
    except OSError:
        pass


def sentinel_daemon(main_pid):
    """Process in charge of shuting down all processes of the server when
    service stops when the pid file is removed or has a bad content (such as a
    wrong pid)."""
    log_sentinel("Starting sentinel daemon")
    last_changed = 0.0
    while True:
        # check status_file, quit all if not ok
        if not PID_FILE.exists():
            break
        mtime = PID_FILE.stat().st_mtime
        if mtime == last_changed:
            # file not modified
            # chek the process is stille running
            try:
                _check_proc_is_running = psutil.Process(pid=main_pid)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                log_sentinel("Error: main Nua server is down")
                break
            sleep(0.5)
            continue
        # file changed (or first cycle)
        last_changed = mtime
        try:
            with open(PID_FILE, "r", encoding="utf8") as f:
                read_pid = int(f.read())
        except OSError:
            break
        if read_pid != main_pid:
            # not same pid ? another server started ?
            log_sentinel(f"PID file got a different PID: {read_pid}")
            break
    # kill main process and its childs
    log_sentinel("Stopping daemon")
    touch_exit_flag()
    unlink_pid_file()
    my_pid = os.getpid()
    parent = psutil.Process(main_pid)
    procs = parent.children(recursive=True)
    procs.append(parent)
    procs = [p for p in procs if p.pid != my_pid]
    for p in procs:
        try:
            p.terminate()
        except:
            pass
    _gone, still_alive = psutil.wait_procs(procs, timeout=2)
    for p in still_alive:
        p.kill()
    # end of myself by returning
    log_sentinel("Exiting")
    unlink_exit_flag()


def start_sentinel(pid):
    """Start the sentinel pseudo daemon as multiprocess child from main
    server."""
    process = mp.Process(target=sentinel_daemon, args=(pid,))
    process.daemon = True
    process.start()


def server_start():
    """Start the main server.

    Main server only duty is to launch and manage sub servers:
      - sentinel server, enforcing the .pid file security.
      - zmq RPC server, in charge of CLI requests
      - in the future: other services
    """
    mp.set_start_method("spawn")
    atexit.register(unlink_pid_file)
    pid = os.getpid()
    PID_FILE.parent.mkdir(exist_ok=True)
    with open(PID_FILE, "w", encoding="utf8") as f:
        f.write(f"{pid}\n")
    start_sentinel(pid)
    # server_init() if needed
    create_base(CONFIG)
    # here launch sub servers
    log_me("Nua server running")
    if CONFIG["server"]["start_zmq_server"]:
        start_zmq_rpc_server(CONFIG)
    while True:
        sleep(1)


def start():
    """Entry point for server "start" command."""
    print("Starting Nua server", file=sys.stderr)
    if PID_FILE.exists():
        msg = f"PID file {PID_FILE} exists, another orchestrator is (probably) running"
        print(msg, file=sys.stderr)
        log(msg)
        return 1
    forker(server_start)
    return 0


def stop():
    """Entry point for server "stop" command."""
    if not PID_FILE.exists():
        msg = "PID file not found, orchestrator is (probably) not running"
        print(msg, file=sys.stderr)
        log(msg)
        unlink_exit_flag()
        return 1
    try:
        with open(PID_FILE, "r", encoding="utf8") as f:
            read_pid = int(f.read())
    except OSError:
        read_pid = 0
    if read_pid:
        log_me("Stopping daemon")
        print("Stopping Nua server", file=sys.stderr)
        # first try to kill directly the main server tree
        try:
            server_proc = psutil.Process(pid=read_pid)  # check server exists
            procs = server_proc.children(recursive=True)
            procs.append(server_proc)
            for p in procs:
                try:
                    p.terminate()
                except (
                    psutil.NoSuchProcess,
                    psutil.AccessDenied,
                    psutil.ZombieProcess,
                ):
                    pass
            _gone, still_alive = psutil.wait_procs(procs, timeout=2)
            for p in still_alive:
                p.kill()
        except psutil.NoSuchProcess:
            msg = "Main Nua server maybe already down"
            print(msg, file=sys.stderr)
        unlink_exit_flag()
    unlink_pid_file()
    log_me("Exiting")

    return 0


def restart():
    """Entry point for server "restart" command."""
    touch_exit_flag()
    stop()
    count = 100  # 10 sec
    while EXIT_FLAG.exists():
        sleep(0.1)
        count -= 1
        if count < 0:
            msg = "Timeout when stopping server daemon: the sentinel server may be down"
            print(msg, file=sys.stderr)
            log(msg)
            # note: we could also store the pid of the sentinel to check it is not down
            unlink_exit_flag()
    return start()


def status():
    """Entry point for server "status" command."""
    # fixme: go further on status details (sub servzrs...)
    if not PID_FILE.exists():
        msg = "PID file not found, orchestrator is (probably) not running."
        print(msg, file=sys.stderr)
        return 1
    try:
        with open(PID_FILE, "r", encoding="utf8") as f:
            read_pid = int(f.read())
    except OSError:
        msg = "Error reading PID file"
        print(msg, file=sys.stderr)
        return 2
    try:
        _check_proc_is_running = psutil.Process(pid=read_pid)
    except psutil.NoSuchProcess:
        msg = f"PID should be {read_pid}, but no process. This is a bug."
        print(msg, file=sys.stderr)
        return 3
    except psutil.AccessDenied:
        msg = f"PID should be {read_pid}, but 'AccessDenied'."
        print(msg, file=sys.stderr)
        return 4
    msg = f"Nua orchestrator is running with PID {read_pid}"
    print(msg, file=sys.stderr)
    return 0


def main(cmd: str) -> int:
    """Entry point if the module is used alone or with main("command")."""
    if cmd == "start":
        return start()
    if cmd == "stop":
        return stop()
    if cmd == "restart":
        return restart()
    if cmd == "status":
        return status()
    print(f"Unknown command: {cmd}", file=sys.stderr)
    return 255  # unknown argument


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
