import re
from os import chdir
from pathlib import Path
from shutil import copy2, copytree

from nua.lib.actions import (  # installed_packages,
    download_extract,
    install_package_list,
    install_psycopg2_python,
    set_php_ini_keys,
    tmp_install_package_list,
)
from nua.lib.shell import chown_r, mkdir_p, rm_fr, sh
from nua.runtime.nua_config import NuaConfig


def main():
    config = NuaConfig(".")

    release = "16.0.3"
    doli_url = f"https://github.com/Dolibarr/dolibarr/archive/{release}.tar.gz"
    packages = [
        "apache2",
        "php",
        "php-cli",
        # "php-mysql",
        "php-pgsql",
        "php-common",
        "php-zip",
        "php-mbstring",
        "php-xmlrpc",
        "php-curl",
        "php-soap",
        "php-gd",
        "php-xml",
        "php-intl",
        "php-ldap",
        "libapache2-mod-php",
        "postgresql-client",
        "unzip",  # ?
    ]
    # "bzip2",
    # "cron",
    # "rsync",
    # "sendmail",
    # "unzip",
    # "zip",
    # "libc-client-dev",
    # "libfreetype6-dev",
    # "libjpeg62-dev",
    # "libkrb5-dev",
    # "libldap2-dev",
    # "libpng-dev",
    # "libpq-dev",
    # "libxml2-dev",
    # "libzip-dev",
    # "build-essential",
    # ]

    # tmp_packages = [
    # "build-essential",
    # "python3-dev",
    # "libsqlite3-dev",
    # "netcat",
    # "libicu-dev",
    # "libssl-dev",
    # "git",
    # ]
    install_package_list(packages, keep_lists=True)
    install_psycopg2_python()  # for db initialialization in start.py

    set_php_ini_keys(
        {
            "allow_url_fopen": "Off",
            "disable_functions": (
                "disable_functions = pcntl_alarm,pcntl_fork,pcntl_waitpid,pcntl_wait,"
                "pcntl_wifexited,pcntl_wifstopped,pcntl_wifsignaled,pcntl_wifcontinued,"
                "pcntl_wexitstatus,pcntl_wtermsig,pcntl_wstopsig,pcntl_signal,"
                "pcntl_signal_get_handler,pcntl_signal_dispatch,pcntl_get_last_error,"
                "pcntl_strerror,pcntl_sigprocmask,pcntl_sigwaitinfo,pcntl_sigtimedwait,"
                "pcntl_exec,pcntl_getpriority,pcntl_setpriority,pcntl_async_signals,"
                "passthru,shell_exec,system,proc_open,popen"
            ),
            "max_execution_time": "60",
            "memory_limit": "256M",
            "open_basedir": "/var/www/localhost/htdocs:/var/www/documents:/var/www/run:/tmp",
            "post_max_size": "64M",
            "session.cookie_samesite": "Lax",
            "session.save_path": "/var/www/run",
            "session.use_strict_mode": "1",
            "upload_max_filesize": "64M",
        },
        "/etc/php/8.1/apache2/php.ini",
    )
    # and maybe:
    # date.timezone = TIMEZONE
    # display_errors = On
    # log_errors = Off

    chdir("/nua/build")
    download_extract(doli_url, "/nua/build")
    src = Path(f"/nua/build/dolibarr-{release}")
    rm_fr("/var/www/html")
    copytree(src / "htdocs", "/var/www/html")
    sh("ln -s /var/www/html /var/www/htdocs")
    copytree(src / "scripts", "/var/www/scripts")
    rm_fr(src)
    mkdir_p("/var/www/documents")
    mkdir_p("/var/www/html/custom")
    chown_r("/var/www", "www-data", "www-data")


if __name__ == "__main__":
    main()
