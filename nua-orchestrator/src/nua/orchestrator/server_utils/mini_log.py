"""Pseudo log system."""
import os
from datetime import datetime, timezone
from pathlib import Path

log_file = None


def log(*args):  # see later log module implementation
    """Basic logger replacement."""
    global log_file
    if log_file is None:
        path = os.environ.get("NUA_LOG_FILE", "")
        if not path:
            return
        log_file = Path(path)
    if not log_file.exists():
        log_file.parent.mkdir(exist_ok=True)
    with open(log_file, "a", encoding="utf8") as f:
        f.write(datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S - "))
        f.write(" ".join(str(x) for x in args))
        f.write("\n")


def log_me(*args):
    """Log with main server identity."""
    log(f"Nua Orc.({os.getpid()}) -", *args)


def log_sentinel(*args):
    """Log with sentinel server identity."""
    log(f"Nua Orc. Sent.({os.getpid()}) -", *args)
