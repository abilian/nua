Warning: use makefile, (or  build from buld_dir)

```
make nua
```

Note: we use the feature of no build.py, only a declaration of a python `wheel`

Note2: build must be successful, but running the appliction is probably not possible
due to use of local database of the host.

This example to test
- a flask basic app
- using the mariadb connector and Nua agent
- declare requirement of mariadb connector vie 'meta-packages' in config
- declare requirement of creation of document-root via config
- connection to a mariadb DB running on local host

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


This package requires the python package mariadb >= 1.1.5post3

sample start command

docker run -it -e --add-host=host.docker.internal:host-gateway nua-flask-mariadb-wheel:1.0-1
