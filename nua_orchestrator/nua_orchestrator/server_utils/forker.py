"""Function to fork a function as an independant daemon."""

import os
from time import asctime
from traceback import format_exc


def close_file_descriptors():
    """Close file descriptors to allow clean POSIX deamon fork."""
    try:
        maxfd = os.sysconf("SC_OPEN_MAX")
    except (AttributeError, ValueError):
        maxfd = 256  # default maximum
    for file_descriptor in range(0, maxfd):
        try:
            os.close(file_descriptor)
        except OSError:
            pass
    # Redirect the standard file descriptors to /dev/null.
    os.open("/dev/null", os.O_RDONLY)  # standard input (0)
    os.open("/dev/null", os.O_RDWR)  # standard output (1)
    os.open("/dev/null", os.O_RDWR)  # standard error (2)


def forker(function, *args):
    """Function to fork a function, does not wait on exit."""
    # first, let's fork
    pid1 = os.fork()
    if pid1 == 0:
        # we are child
        os.setsid()
        # second fork
        pid2 = os.fork()
        if pid2 == 0:
            # we are the second child
            try:
                close_file_descriptors()
                function(*args)
            except Exception:
                err_file = os.environ.get("NUA_LOG_FILE", "")
                if not err_file:
                    return
                with open(err_file, "a+", encoding="utf8") as f:
                    f.write("-" * 40)
                    f.write("\n")
                    f.write(format_exc(50))
                    f.write(asctime())
                    f.write("\n")
                    f.write("-" * 40)
                    f.write("\n")
            finally:
                os._exit(0)
        else:
            # still 1st child
            try:
                # do not block
                os.waitpid(pid2, os.WNOHANG)
            except:
                pass
            finally:
                os._exit(0)
    else:
        # we are still there, continue our duty on
        try:
            os.waitpid(pid1, 0)
        except:
            pass
        return
