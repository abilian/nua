# Nua Agent

The `nua-agent` package is included in every Nua application image.

It will provide the following features (TBC):

-   Application licycle management
-   Smoke tests and health checks
-   Logging and monitoring

## Content

`nua-agent` provides:

-   `nua_config`: library to read the embedded `nua-config` file (introspection),
-   `app_builder`: actual builder of the application inside the Docker image.
-   `db`: collection of tools to manage databases
