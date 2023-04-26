# Nua Agent

[Nua](https://nua.rocks/) is an open source, self-hosted cloud platform project (a PaaS - platform as a service).

This packaged is used internally. The main entry point is the `nua` command line tool (see: [Nua on PyPI](https://pypi.org/project/nua/) or [nua-cli on GitHub](https://github.com/abilian/nua/tree/main/nua-cli)).

The `nua-agent` package is included in every Nua application image.

It will provide the following features (TBC):

-   Application licycle management
-   Smoke tests and health checks
-   Logging and monitoring

## Content

`nua-agent` provides:

- `nua_config`: library to read the embedded `nua-config` file (introspection),
- `app_builder`: actual builder of the application inside the Docker image.
- `db`: collection of tools to manage databases
