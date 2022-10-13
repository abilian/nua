"""Nua mariadb related commands.

WIP

To remove all mariadb packages:
sudo apt-get remove --purge mariadb-server-10.6 mariadb-client
sudo apt-get autoremove
sudo apt-get autoclean

sudo rm /var/lib/mysql/ib_logfile0
sudo rm /var/lib/mysql/ib_logfile1

sudo apt-get install mariadb-server-10.6

sudo apt-get install libmariadb3 libmariadb-dev
"""
import functools
import os
import re
from pathlib import Path
from time import sleep

import mariadb

from .actions import install_package_list, installed_packages
from .exec import exec_as_root, exec_as_root_daemon
from .gen_password import gen_password
from .rich_console import print_magenta, print_red
from .shell import chown_r, sh

MARIADB_VERSION = "10.6"
POSTGRES_CONF_PATH = Path("/todo/etc/mariadbql/14/main")
# RE_ANY_PG = re.compile(r"^mariadbql-[0-9\.]+/")
RE_PORT = re.compile(r"\s*port\s*=\s*(\d+)")
RE_COMMENT = re.compile(r"\s*#")

RE_LISTEN = re.compile(r"\s*listen_addresses\s*=(.*)$")
RE_BIND_ADD = re.compile(r"^(\s*bind-address\s*=)(.*)$")
# # S105 Possible hardcoded password
NUA_MARIADB_PWD_FILE = ".mariadb_pwd"  # noqa S105


def mariadb_pwd() -> str:
    """Return the 'root' user DB password of mariadb.
      - When used in container context, the env variable NUA_MARIADB_PASSWORD should
        contain the password.
      - When used in nua-orchestrator context, read the password from local file.

    For orchestrator context, assuming this function can only be used *after* password
    was generated (or its another bug).

    Rem.: No cache. Rarely used function and pwd can be changed."""
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


def set_mariadb_pwd(password: str) -> bool:
    """Set mariadb root password for local instance of mariadb.

    The password is stored in clear in Nua home. In future version, it could be
    replaced by SSL key, thus gaining the ability to have encyption of streams and
    expiration date.
    Basically we need clear password somewhere. Since this password is only used
    by Nua scripts (if Nua is the only user of local mariadb DB), it could also be
    generated / erased at each invocation.
    No test of min password length in this function.
    """
    r_pwd = repr(password)
    exec_as_root("systemctl stop mariadb")
    exec_as_root_daemon("mariadbd-safe --skip-grant-tables --skip-networking")
    sleep(1)
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


def mariadb_run_environment(_unused: dict) -> dict:
    """Return a dict of environ variable for docker.run().

    Actually, returns the DB mariadb password.
    This function to be used in orchestrator environment, thus the password will
    be read from host file.
    """
    return {"NUA_MARIADB_PASSWORD": mariadb_pwd()}


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
            "mariadb-client",
        ],
        update=False,
        clean=False,
        rm_lists=False,
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
    return False


def mariadb_check_installed() -> bool:
    """Check that mariadb is installed locally."""
    test = _mariadb_check_installed_version()
    if test:
        test = _mariadb_check_std_port()
    return test
    # ensure db started
    # sudo systemctl start mariadbql


def _mariadb_check_installed_version() -> bool:
    package = f"mariadb-server-{MARIADB_VERSION}/"
    found = [s for s in installed_packages() if s.startswith(package)]
    if not found:
        print_red(f"Required package not installed: {package}")
        return False
    return True


def _mariadb_check_config_port(path: Path) -> str:
    with open(path, "r", encoding="utf8") as rfile:
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


@functools.cache
def mariadb_check_listening(gateway: str) -> bool:
    """TODO

    heck at deploy time that the mariadb daemon is listening on the gateway port
    of the docker service (ip passed as parameter).

    This is launched for every deployed image (so cached).
    """

    if not mariadb_check_installed():
        return False
    path = Path("/etc/mysql/mariadb.cnf")
    if not path.is_file():
        print_red(f"Mariadb config file not found: {path}")
        return False
    return True
    # return _actual_check_listening(gateway, path)


#
# def _actual_check_listening(gateway: str, path: Path) -> bool:
#     with open(path, "r", encoding="utf8") as rfile:
#         for line in rfile:
#             if RE_COMMENT.match(line):
#                 continue
#             if (listen_match := RE_LISTEN.match(line)) is not None:
#                 listening = listen_match[1].strip()
#                 return _add_gateway_address(listening, gateway)
#     return _add_gateway_address("", gateway)
#


def allow_docker_connection():
    """
    Check at deploy time that the mariadb_hba.conf file permit connexion.

    Must be run as root at bootstrap time.
    """
    # path = Path("/etc/mysql/mariadb.conf.d/50-server.cnf")
    # if not path.is_file():
    #     print_red(f"Mariadb config file not found: {path}")
    #     return False
    # content = path.read_text(encoding="utf8")
    # address = "172.16.0.0/12"
    # content = re.sub(
    #     r"^(\s*bind-address\s*=)(.*)$", f"\g<1> {address}", content, flags=re.M
    # )
    # path.write_text(content, encoding="utf8")
    path = Path("/etc/mysql/mariadb.conf.d/90-nua.cnf")
    content = "[mysqld]\nskip-networking=0\nskip-bind-address\n"
    path.write_text(content, encoding="utf8")


#
# def _save_config_gateway_address(content: str):
#     src_path = Path("~/nua_listening_docker.conf.tmp").expanduser()
#     with open(src_path, "w", encoding="utf8") as wfile:
#         wfile.write(content)
#     dest_path = POSTGRES_CONF_PATH / "conf.d" / "nua_listening_docker.conf"
#     cmd = f"sudo mv -f {src_path} {dest_path}"
#     sh(cmd, show_cmd=False)
#     cmd = f"sudo chown mariadb:mariadb {dest_path}"
#     sh(cmd, show_cmd=False)
#     cmd = f"sudo chmod 644 {dest_path}"
#     sh(cmd, show_cmd=False)

#
# def _add_gateway_address(listening: str, gateway: str) -> bool:
#     """
#     TODO
#
#     """
#     return
#     if not listening:
#         content = f"listen_addresses = 'localhost, {gateway}'\n"
#         _save_config_gateway_address(content)
#         return True
#     if gateway in listening or "*" in listening:
#         return True
#     if listening.endswith("'"):
#         value = f"{listening[:-1]}, {gateway}'"
#     elif listening.endswith('"'):
#         value = f'{listening[:-1]}, {gateway}"'
#     else:  # dubious
#         value = f"'{listening}, {gateway}'"
#     content = f"listen_addresses = {value}'\n"
#     _save_config_gateway_address(content)
#     return True


def mariadb_restart_service():
    """Restart mariadb service."""
    cmd = "sudo systemctl restart mariadb"
    sh(cmd)


def mariadb_setup_db_user(host: str, dbname: str, user: str, password: str):
    """Create a mariadb user if needed."""
    if not mariadb_user_exist(host, user):
        mariadb_user_create(host, user, password)
    if not mariadb_db_exist(host, dbname):
        mariadb_db_create(host, dbname, user)


def mariadb_remove_db_user(host: str, dbname: str, user: str):
    """Remove a mariadb user if needed."""
    if mariadb_db_exist(host, dbname):
        mariadb_db_drop(host, dbname)
    if mariadb_user_exist(host, user):
        mariadb_user_drop(host, user)


def mariadb_db_drop(host: str, dbname: str):
    """Basic drop database."""
    connection = mariadb.connect(host=host, user="root", password=mariadb_pwd())
    cursor = connection.cursor()
    query = f"drop database [if exists] `{dbname}`"
    cursor.execute(query)
    connection.close()


def mariadb_db_dump(dbname: str, options_str: str = ""):
    """Basic mariadb_dump call.

    FIXME: not ok for remote host
    """
    cmd = f"mariadb-dump {dbname} {options_str}"
    exec_as_root(cmd)


def mariadb_user_drop(host: str, user: str) -> bool:
    """Drop user (wip, not enough)."""
    connection = mariadb.connect(host=host, user="root", password=mariadb_pwd())
    cursor = connection.cursor()
    query = "DROP USER IF EXISTS ?"
    cursor.execute(query, (user,))
    connection.close()


def mariadb_user_exist(host: str, user: str) -> bool:
    """Test if a mariadb user exists."""
    connection = mariadb.connect(host=host, user="root", password=mariadb_pwd())
    cursor = connection.cursor()
    query = "SELECT EXISTS(SELECT 1 FROM mysql.user WHERE user = ?"  # noqa S608
    cursor.execute(query, (user,))
    (count,) = cursor.fetchone()
    connection.close()
    return count != 0


def mariadb_user_create(host: str, user: str, password: str):
    """Create a mariadb user.

    Assuming standard port 3306
    """
    connection = mariadb.connect(host=host, user="root", password=mariadb_pwd())
    cursor = connection.cursor()
    query = "CREATE USER IF NOT EXISTS ? IDENTIFIED BY ?"
    cursor.execute(query, (user, password))
    connection.commit()
    connection.close()


def mariadb_db_create(host: str, dbname: str, user: str):
    """Create a mariadb DB.

    Assuming standard port 3306
    """
    connection = mariadb.connect(host=host, user="root", password=mariadb_pwd())
    cursor = connection.cursor()
    query = f"CREATE DATABASE `{dbname}`"
    cursor.execute(query)
    connection.close()


def mariadb_db_exist(host: str, dbname: str) -> bool:
    "Test if the named mariadb database exists."
    connection = mariadb.connect(host=host, user="root", password=mariadb_pwd())
    cursor = connection.cursor()
    query = "SHOW DATABASES LIKE `{dbname}`"
    nb = cursor.execute(query, (dbname,))
    connection.close()
    return nb > 0


def mariadb_db_table_exist(
    host: str, dbname: str, user: str, password: str, table: str
) -> bool:
    """Check if the named database exists (for host, connecting as user), assuming
    DB exists."""
    connection = mariadb.connect(host=host, dbname=dbname, user=user, password=password)
    cursor = connection.cursor()
    query = "SELECT COUNT(*) FROM information_schema WHERE TABLE_NAME=?"
    cursor.execute(query, (table,))
    result = cursor.fetchone()
    count = result[0] if result else 0
    connection.close()
    return count > 0
