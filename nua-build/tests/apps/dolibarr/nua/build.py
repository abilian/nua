from os import chdir, listdir
from pathlib import Path
from shutil import copytree

from nua.lib.actions import (  # installed_packages,
    download_extract,
    install_package_list,
    install_psycopg2_python,
    set_php_ini_keys,
)
from nua.lib.shell import chmod_r, chown_r, mkdir_p, rm_fr, sh
from nua.runtime.nua_config import NuaConfig


def main():
    config = NuaConfig(".")
    params = config.build
    source = params["source_url"].format(**params)
    install_package_list(params["packages"], keep_lists=True)
    if params.get("postgres", False):
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
            "open_basedir": "/var/www/html:/var/www/localhost/htdocs:/var/www/documents:/var/www/run:/tmp",
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
    response = download_extract(source, "/nua/build")
    print(response)
    src = Path(response)
    # src = Path(f"/nua/build/dolibarr-{params['version']}")
    # src.rename("dolibarr")
    # chmod_r("/nua/build/dolibarr/scripts", 0o555)
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
