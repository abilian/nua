from nua.lib.common.exec import exec_as_root

env = {
    "APACHE_RUN_USER": "www-data",
    "APACHE_RUN_GROUP": "www-data",
    "APACHE_PID_FILE": "/var/run/apache2/apache2.pid",
    "APACHE_RUN_DIR": "/var/run/apache2",
    "APACHE_LOCK_DIR": "/var/lock/apache2",
}

exec_as_root("/usr/sbin/apachectl -D FOREGROUND", env=env)
