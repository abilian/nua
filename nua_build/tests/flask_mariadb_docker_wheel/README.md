This example to test
- a flask basic app
- using the mariadb connector and Nua runtime
- connection to a mariadb DB running on an official docker image of Mariadb

Warning:

MariaDB does not provide wheel package for the mariadb connector for python on linux,
and the build of the python package may fail when launched from Pip virtual env.

So we do our own wheel from the source before, then explicitely install from the wheel.

As such, the better way to build the Nua image is to use the local Makefile:
    make


Testing with nua-orchestrator:

make a basic `test.toml` file with:

    [[site]]
    image = "nua-flask-mariadb-docker-wheel"
    domain = "test1.example.com"

then:

    nua deploy test.toml
