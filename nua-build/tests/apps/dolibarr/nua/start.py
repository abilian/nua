import os
import secrets
from datetime import datetime, timezone
from pathlib import Path

# import psycopg2
from nua.lib.actions import jinja2_render_file
from nua.lib.exec import exec_as_root, sudo_cmd_as_user
from nua.lib.shell import chmod_r, chown_r

# Nua shortcuts to manage postgres operations
from nua.runtime.postgres_manager import PostgresManager
from packaging.version import Version

# set in CMD_DB_HOST the actual value of the just created docker private network
# This laybe not needed now (see [instance.db_host])
# DOLI_DB_HOST = os.environ.get("NUA_DATABASE_HOST")
# env = os.environ.copy()
# env["DOLI_DB_HOST"] = os.environ.get("NUA_DATABASE_HOST")

print(os.environ)

INSTALLED_VERSION = Path("/var/www/documents/installed.txt")
INSTALL_LOCK = Path("/var/www/documents/install.lock")
NOW = datetime.now(tz=timezone.utc).isoformat()


def setup_db():
    """Find or create the required DB for app user.

    In this example The DB is on remote docker container.
    """
    manager = PostgresManager(
        host=os.environ.get("DOLI_DB_HOST"), port=os.environ.get("DOLI_DB_PORT")
    )
    manager.setup_db_user(
        os.environ.get("DOLI_DB_NAME"),
        os.environ.get("DOLI_DB_USER"),
        os.environ.get("DOLI_DB_PASSWORD"),
    )


def setup_dirs():
    path = Path("/var/www/documents")
    path.mkdir(parents=True, exist_ok=True)
    chown_r(path, "www-data", "root")
    chmod_r(path, 0o664, 0o775)
    path = Path("/var/www/html/conf")
    path.mkdir(parents=True, exist_ok=True)
    chown_r(path, "www-data", "root")
    path.chmod(0o550)
    path = Path("/var/www/html/install")
    path.mkdir(parents=True, exist_ok=True)
    chown_r(path, "www-data", "root")
    chmod_r(path, 0o664, 0o775)
    # path = Path("/run/apache2")
    # path.chmod(0o770)


def setup_conf_php():
    conf = Path("/var/www/html/conf/conf.php")
    if not conf.is_file():
        data = os.environ.copy()
        data["DATE"] = NOW
        data["CRYPTKEY"] = secrets.token_hex(32)
        jinja2_render_file(
            template="/nua/build/nua/config_template.php",
            dest=conf,
            data=data,
        )
    chown_r(conf, "www-data", "root")
    conf.chmod(0o440)


def check_version():
    if not INSTALLED_VERSION.is_file():
        return
    installed = Version(INSTALLED_VERSION.read_text())
    current = Version(os.environ.get("DOLI_VERSION"))
    if installed > current:
        message = (
            f"Dolibarr installed data version: {installed}\n"
            "Dolibarr package version: {current}\n"
            "Impossible to start with data of higher version."
        )
        raise ValueError(message)


def dolibarr_init():
    pass
    # echo "Dolibarr initialization..."


# rsync_options="--verbose --archive --chmod a-w --chown apache:root"
#
# rsync $rsync_options --delete --exclude /conf/ --exclude /custom/ --exclude /theme/ /nua/build/dolibarr/htdocs/ /var/www/html/
#
# for dir in conf custom; do
# 	if [ ! -d /var/www/html/"$dir" ] || directory_empty /var/www/html/"$dir"; then
# 		rsync $rsync_options --include /"$dir"/ --exclude '/*' /nua/build/dolibarr/htdocs/ /var/www/html/
# 	fi
# done
#
# # The theme folder contains custom and official themes. We must copy even if folder is not empty, but not delete existing content
# for dir in theme; do
# 	rsync $rsync_options --include /"$dir"/ --exclude '/*' /nua/build/dolibarr/htdocs/ /var/www/html/
# done


def dolibarr_upgrade():
    if not INSTALLED_VERSION.is_file():
        return
    installed = Version(INSTALLED_VERSION.read_text())
    current = Version(os.environ.get("DOLI_VERSION"))
    if current == installed:
        return
    # upgrade
    # echo "Dolibarr upgrade from $installed_version to $image_version..."
    #
    # if [ -f /var/www/documents/install.lock ]; then
    #     rm /var/www/documents/install.lock
    # fi
    #
    # base_version=(${installed_version//./ })
    # target_version=(${image_version//./ })
    #
    # # Call upgrade scripts
    # chmod 660 /var/www/html/conf/conf.php
    # run_as "cd /var/www/html/install/ && php upgrade.php ${base_version[0]}.${base_version[1]}.0 ${target_version[0]}.${target_version[1]}.0"
    # run_as "cd /var/www/html/install/ && php upgrade2.php ${base_version[0]}.${base_version[1]}.0 ${target_version[0]}.${target_version[1]}.0"
    # run_as "cd /var/www/html/install/ && php step5.php ${base_version[0]}.${base_version[1]}.0 ${target_version[0]}.${target_version[1]}.0"
    # chmod 440 /var/www/html/conf/conf.php


def touch_install_lock():
    INSTALL_LOCK.write_text(f"Installed {NOW}")
    chown_r(INSTALL_LOCK, "www-data", "www-data")
    INSTALL_LOCK.chmod(0o440)


def dolibarr_first_install():
    if INSTALLED_VERSION.is_file() or INSTALL_LOCK.is_file():
        return
    forced = Path("/var/www/html/install/install.forced.php")

    data = os.environ.copy()
    data["DATE"] = NOW
    jinja2_render_file(
        template="/nua/build/nua/install_template.php",
        dest=forced,
        data=data,
    )
    chown_r(forced, "www-data", "root")
    forced.chmod(0o660)
    sudo_cmd_as_user(
        cmd="php step2.php set", user="www-data", cwd="/var/www/html/install"
    )
    lang = os.environ.get("LANG") or "fr_FR"
    pwd = os.environ["DOLI_ADMIN_PASSWORD"]
    sudo_cmd_as_user(
        cmd=f"php step5.php 0 0 {lang} set {pwd} {pwd} {pwd}",
        user="www-data",
        cwd="/var/www/html/install",
    )
    forced.chmod(0o440)
    touch_install_lock()


def last_setup():
    chown_r("/var/www/html/custom", "www-data", "root")
    Path("/var/www/html/custom").chmod(0o775)
    if INSTALL_LOCK.is_file():
        INSTALLED_VERSION.write_text(f"{os.environ.get('DOLI_VERSION')}\n")


def setup_dolibarr():
    setup_dirs()
    setup_conf_php()
    check_version()
    dolibarr_init()
    dolibarr_upgrade()
    dolibarr_first_install()
    last_setup()


setup_dolibarr()
setup_db()

env = {
    "APACHE_RUN_USER": "www-data",
    "APACHE_RUN_GROUP": "www-data",
    "APACHE_PID_FILE": "/var/run/apache2/apache2.pid",
    "APACHE_RUN_DIR": "/var/run/apache2",
    "APACHE_LOCK_DIR": "/var/lock/apache2",
}
exec_as_root("/usr/sbin/apachectl -D FOREGROUND", env=env)
