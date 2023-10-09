"""Nua mariadb orchestrator commands.

WIP

To remove all mariadb packages::

    sudo apt-get remove --purge mariadb-server-10.6 mariadb-client
    sudo apt-get autoremove sudo apt-get autoclean

    sudo rm /var/lib/mysql/ib_logfile0 sudo rm /var/lib/mysql/ib_logfile1

    sudo apt-get install mariadb-server-10.6

    sudo apt-get install libmariadb3 libmariadb-dev
"""
import os
import re
from pathlib import Path
from time import sleep

from nua.lib.actions import install_package_list, installed_packages
from nua.lib.console import print_magenta, print_red
from nua.lib.exec import exec_as_root, exec_as_root_daemon
from nua.lib.gen_password import gen_password
from nua.lib.panic import warning
from nua.lib.shell import chown_r, sh

MARIADB_VERSION = "10.6"
RE_PORT = re.compile(r"\s*port\s*=\s*(\d+)")
RE_COMMENT = re.compile(r"\s*#")
NUA_MARIADB_PWD_FILE = ".mariadb_pwd"  # noqa S105


def mariadb_pwd() -> str:
    """Return the 'root' user DB password of mariadb.

      - When used in container context, the env variable NUA_MARIADB_PASSWORD should
        contain the password.
      - When used in nua-orchestrator context, read the password from local file.

    For orchestrator context, assuming this function can only be used *after* password
    was generated (or its another bug).

    Rem.: No cache. Rarely used function and pwd can be changed.
    """
    pwd = os.environ.get("NUA_MARIADB_PASSWORD")
    if pwd:
        return pwd
    file_path = Path(os.path.expanduser("~nua")) / NUA_MARIADB_PWD_FILE
    return file_path.read_text(encoding="utf8").strip()


def set_random_mariadb_pwd() -> bool:
    print_magenta("Setting Mariadb password")
    return set_mariadb_pwd(gen_password(24))


def _store_mariadb_password(password: str):
    """Store the password in "~nua/.mariadb_pwd".

    Expect to be run either by root or nua.
    """
    file_path = Path(os.path.expanduser("~nua")) / NUA_MARIADB_PWD_FILE
    file_path.write_text(f"{password}\n", encoding="utf8")
    chown_r(file_path, "nua")
    os.chmod(file_path, 0o600)  # noqa: S103


def set_mariadb_pwd(password: str, any_ip=True) -> bool:
    """Set mariadb root password for local instance of mariadb.

    The password is stored in clear in Nua home. In future version, it
    could be replaced by SSL key, thus gaining the ability to have
    encyption of streams and expiration date. Basically we need clear
    password somewhere. Since this password is only used by Nua scripts
    (if Nua is the only user of local mariadb DB), it could also be
    generated / erased at each invocation. No test of min password
    length in this function.
    """
    r_pwd = repr(password)
    exec_as_root("systemctl stop mariadb")
    exec_as_root_daemon("mariadbd-safe --skip-grant-tables --skip-networking")
    sleep(1)

    if any_ip:
        cmd = (
            'mariadb -u root  -e "FLUSH PRIVILEGES; '
            f"ALTER USER 'root'@'localhost' IDENTIFIED BY {r_pwd}; "
            f"CREATE OR REPLACE USER 'root'@'%' IDENTIFIED BY {r_pwd}; "
            "GRANT ALL PRIVILEGES ON *.* TO 'root'@'%' WITH GRANT OPTION;\""
        )
    else:
        cmd = (
            'mariadb -u root  -e "FLUSH PRIVILEGES; '
            f"ALTER USER 'root'@'localhost' IDENTIFIED BY {r_pwd};\""
        )
    exec_as_root(cmd, show_cmd=False)
    sleep(1)

    pid = sh(
        "sudo cat /run/mysqld/mysqld.pid", show_cmd=False, capture_output=True
    ).strip()
    exec_as_root(f"kill {pid}")
    sleep(1)

    exec_as_root("systemctl start mariadb")
    _store_mariadb_password(password)
    print(mariadb_status(password))
    return True


def mariadb_status(password: str) -> str:
    cmd = f"mariadb -u root -p{password} -e 'status'"
    return sh(cmd, capture_output=True, show_cmd=False)


def mariadb_version() -> str:
    maria = Path("/usr/bin/mariadb")
    if not maria.exists():
        return ""
    cmd = f"{maria} --version"
    line = sh(cmd, show_cmd=False, capture_output=True)
    if line:
        print(line)
    parts = line.split()
    if len(parts) > 3 and parts[3] == "Distrib":
        return parts[4]
    return ""


def bootstrap_install_mariadb() -> bool:
    """Installing the required mariadb version locally.

    Need to be executed as root at nua install stage.
    """
    print_magenta(f"Installation of mariadb version {MARIADB_VERSION}")
    # detect prior installation of other versions:
    if not _mariadb_verify_no_prior_installation():
        return False
    install_package_list(
        [
            f"mariadb-server-{MARIADB_VERSION}",
            "libmariadb3",
            "libmariadb-dev",
            # "mariadb-client",
        ],
        clean=False,
        keep_lists=True,
    )
    allow_docker_connection()
    return mariadb_check_installed()


def _mariadb_verify_no_prior_installation() -> bool:
    conf_path = Path("/etc/mysql/mariadb.cnf")
    if not conf_path.is_file():
        return True
    existing_version = mariadb_version()
    if existing_version.startswith(MARIADB_VERSION):
        return True
    print_red(
        "Some Mariadb installation was found and need to be removed by commands like:"
    )
    print_red("    apt purge -y mariadb-server-10.6")
    print_red("    apt autoremove -y")
    print_red("Installation will continue, but some package using Mariadb may fail.")
    return True


def mariadb_check_installed() -> bool:
    """Check that mariadb is installed locally."""
    test = _mariadb_check_installed_version()
    if test:
        test = _mariadb_check_std_port()
    return test
    # ensure db started
    # sudo systemctl start mariadbql


def _mariadb_check_installed_version() -> bool:
    package = f"mariadb-server-{MARIADB_VERSION}"
    if package in installed_packages():
        return True
    warning(f"Required package not installed: {package}")
    return False


def _mariadb_check_config_port(path: Path) -> str:
    with open(path, encoding="utf8") as rfile:
        for line in rfile:
            if RE_COMMENT.match(line):
                continue
            if (port_match := RE_PORT.match(line)) is not None:
                return port_match[1].strip()
    return ""


def _mariadb_check_std_port() -> bool:
    path = Path("/etc/mysql/mariadb.cnf")
    if not path.is_file():
        print_red(f"Mariadb config file not found: {path}")
        return False
    port = _mariadb_check_config_port(path)
    if port == "3306" or not port:
        # assuming use of default port of 3306
        return True
    print_red("Mariadb is expected on standard port 3306, check configuration.")
    return False


def allow_docker_connection():
    """Check at deploy time that the mariadb_hba.conf file permit connexion.

    Must be run as root at bootstrap time.
    """
    path = Path("/etc/mysql/mariadb.conf.d/90-nua.cnf")
    content = "[mysqld]\nskip-networking=0\nskip-bind-address\n"
    path.write_text(content, encoding="utf8")


def mariadb_restart_service():
    """Restart mariadb service."""
    cmd = "sudo systemctl restart mariadb"
    sh(cmd)
