# Nua Runtime

The `nua-runtime` package is included in every Nua application image.

It will provide the following features (TBC):

-   Application licycle management
-   Smoke tests and health checks
-   Logging and monitoring

## Content

`nua-runtime` provides:

-   `nua_config`: library to read the embeded `nua-config` file (introspection),
-   `nua_build_setup_app`: actual builder of the application inside the Docker image.
-   `db`: collection of tools to manage databases
