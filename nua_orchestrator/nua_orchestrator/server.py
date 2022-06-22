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
from contextlib import suppress
from pathlib import Path
from time import sleep

import psutil

from . import config
from .server_utils.forker import forker
from .server_utils.mini_log import log, log_me, log_sentinel
from .zmq_rpc_server import start_zmq_rpc_server

# NOTE: /tmp is not ideal, but /run would require some privileges: see later.
# see later for log module implementation
os.environ["NUA_LOG_FILE"] = config.get("server", "log_file")


def unlink_pid_file():
    """Unlink the server pid file, no fail on error."""
    pid_file = Path(config.get("server", "pid_file"))
    if pid_file.exists():
        with suppress(OSError):
            pid_file.unlink(missing_ok=True)


def touch_exit_flag():
    """Create a temporary flag file, to secure server stop/start ordering."""
    exit_flag = Path(config.get("server", "exit_flag"))
    if exit_flag.exists():
        return
    exit_flag.parent.mkdir(exist_ok=True)

    with open(exit_flag, "w", encoding="utf8") as f, suppress(OSError):
        f.write("\n")


def unlink_exit_flag():
    """Unlink the EXIT_FLAG, no fail on error."""
    exit_flag = Path(config.get("server", "exit_flag"))
    with suppress(OSError):
        exit_flag.unlink(missing_ok=True)


def sentinel_daemon(main_pid):
    """Process in charge of shuting down all processes of the server when
    service stops when the pid file is removed or has a bad content (such as a
    wrong pid)."""
    pid_file = Path(config.get("server", "pid_file"))
    log_sentinel("Starting sentinel daemon")
    last_changed = 0.0
    while True:
        # check status_file, quit all if not ok
        if not pid_file.exists():
            break
        mtime = pid_file.stat().st_mtime
        if mtime == last_changed:
            # file not modified
            # chek the process is stille running
            try:
                # check proc is running
                psutil.Process(pid=main_pid)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                log_sentinel("Error: main Nua server is down")
                break
            sleep(0.5)
            continue
        # file changed (or first cycle)
        last_changed = mtime
        try:
            with open(pid_file, "r", encoding="utf8") as f:
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
        with suppress(Exception):
            p.terminate()
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
    pid_file = Path(config.get("server", "pid_file"))
    mp.set_start_method("spawn")
    atexit.register(unlink_pid_file)
    pid = os.getpid()
    pid_file.parent.mkdir(exist_ok=True)
    with open(pid_file, "w", encoding="utf8") as f:
        f.write(f"{pid}\n")
    start_sentinel(pid)
    # server_init() if needed

    # here launch sub servers
    log_me("Nua server running")
    if config.get("server", "start_zmq_server"):
        start_zmq_rpc_server()
    while True:
        sleep(1)


def start(_cmd: str = ""):
    """Entry point for server "start" command."""
    print("Starting Nua server", file=sys.stderr)
    pid_file = Path(config.get("server", "pid_file"))
    if pid_file.exists():
        msg = f"PID file '{pid_file.name}' exists, another orchestrator is (probably) running"
        print(msg, file=sys.stderr)
        log(msg)
        return 1
    forker(server_start)
    return 0


def stop(_cmd: str = ""):
    """Entry point for server "stop" command."""
    pid_file = Path(config.get("server", "pid_file"))
    if not pid_file.exists():
        msg = "PID file not found, orchestrator is (probably) not running"
        print(msg, file=sys.stderr)
        log(msg)
        unlink_exit_flag()
        return 1
    try:
        with open(pid_file, "r", encoding="utf8") as f:
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
                with suppress(
                    psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess
                ):
                    p.terminate()
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


def restart(cmd: str = ""):
    """Entry point for server "restart" command."""
    exit_flag = Path(config.get("server", "exit_flag"))
    touch_exit_flag()
    stop(cmd)
    count = 100  # 10 sec
    while exit_flag.exists():
        sleep(0.1)
        count -= 1
        if count < 0:
            msg = "Timeout when stopping server daemon: the sentinel server may be down"
            print(msg, file=sys.stderr)
            log(msg)
            # note: we could also store the pid of the sentinel to check it is not down
            unlink_exit_flag()
    return start(cmd)


def _check_status_1():
    pid_file = Path(config.get("server", "pid_file"))
    if pid_file.exists():
        return 0, ""
    return 1, "PID file not found, orchestrator is (probably) not running."


def _check_status_2():
    pid_file = Path(config.get("server", "pid_file"))
    stat = 0
    msg = ""
    try:
        with open(pid_file, "r", encoding="utf8") as f:
            read_pid = int(f.read())
    except OSError:
        stat, msg = 2, "Error reading PID file."
    if not stat:
        try:
            psutil.Process(pid=read_pid)
        except psutil.NoSuchProcess:
            stat, msg = 3, f"PID should be {read_pid}, but no process. This is a bug."
        except psutil.AccessDenied:
            stat, msg = 4, f"PID should be {read_pid}, but 'AccessDenied'."
        else:
            stat, msg = 0, f"Nua orchestrator is running with PID {read_pid}"
    return stat, msg


def status(_cmd: str = "") -> int:
    """Entry point for server "status" command."""
    # fixme: go further on status details (sub servers...)
    stat, msg = _check_status_1()
    if not stat:
        stat, msg = _check_status_2()
    print(msg, file=sys.stderr)
    return stat
