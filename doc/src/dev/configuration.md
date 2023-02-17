# Configuring a Nua project

## The `nua-config` file

This is the cornerstone of a Nua managed application. This file centralises the metadata describing the application, the description of the application's _build_ steps, the required resources (databases, etc.) and the default values (environment, configuration files).

The content of this file is interpreted at all stages of the life cycle of an application managed by Nua: first, during the *build*, to build an OCI image and then, during the *run*, by the orchestrator to deploy one or more instances of the image, with all the resources they require, and then to maintain them in operational condition.

The syntax used is the TOML language, but Nua also accepts YAML and JSON.

## An example of a commented `nua-config` file: **HedgeDoc**

HedgeDoc (<https://hedgedoc.org/>) is a collaborative Markdown document editing application, one of the first to be packaged with Nua. It is a Nodejs application that uses the classic *build* tools for this ecosystem: `package.json` and `npm`.

### Section `metadata`

The `nua-config.toml` file starts with a block of metadata that describes the application in the classic way:

```toml
[metadata]
id = "hedgedoc"
version = "1.9.6"
release = 13
title = "Hedgedoc"
author = "Hedgedoc developers"
tagline = "The best platform to write and share markdown"
website = "https://hedgedoc.org/"
tags = ["Markdown", "Documentation", "Collaboration"]
license = "AGPL-3.0 license"
src-url = "https://github.com/hedgedoc/hedgedoc/releases/download/{version}/hedgedoc-{version}.tar.gz"
checksum = "dfd0fca006f9075f072df058476ea542adb32b63964afb2985211e1114ab333e"
```

Metadata is used as a basis for naming images, volumes and resources, but also for cataloguing applications, and eventually making them available on a marketplace, either internal to the organisation or offered by an operator.

When a `README` file is available, it is also taken into account.

NB: Compound keywords are recognized with either `src-url` or `src_url` spelling, `{}` braces are interpreted (via Python `f-string`).

### `build` section

The `build` section specifies the environment and, if applicable, the specific actions to be performed to build the executable artifact(s) of the application. Nua already supports the main languages on the market (Python, PHP, Node, Ruby, Java, Go...) with their respective supply chains (e.g. `pip` for Python, `gem` for Ruby, etc.), support which can be extended by *plugins*. Where a Dockerfile already exists

```toml
[build]
builder = "node-14"
run-packages = [
    "fontconfig",
    "fonts-noto"
]
build-packages = [
    "build-essential",
    "python3-dev",
    "libsqlite3-dev",
    "netcat",
    "libicu-dev",
    "libssl-dev",
    "git",
]
test = "test -f /nua/build/hedgedoc/healthcheck.mjs"
```

The declarations in the _build_ section rely as much as possible on declarative mode, auto-detection and default files. Here we are dealing with a Node application, which is normally auto-detected by the presence of a `package.json` file. However, as the current version of Hedgedoc requires a specific version of Node, this configuration item must be specified by the `builder = "node-14"` directive.

Build-packages are packages which are needed for the 'build' phase of the application, but which can be removed afterwards, in order to get a reasonably sized image.

Finally, the `test` tag declares a "smoke test" to verify that the application is installed correctly.

In addition to these declarations, if the `nua-build` tool detects a local folder named `nua/`, its contents are taken into account and included in the image. If a file named `build.py` is detected, it will be run in addition. Similarly a `start.py` file may contain the container startup directives. All of these are configurable in the `build` section.


### Section `env`

This section allows you to specify the variables that will be injected into the application's environment when it starts, following the principles of *12 factor apps*.

```toml
[env]
CMD_DOMAIN = "localhost"
NODE_ENV = "production"
# ... (truncated list)
CMD_DB_PORT = "5432"
CMD_DB_DIALECT = "postgres"
# Dynamic variables
CMD_DB_HOST = { from="database", key="hostname" }
CMD_DB_DATABASE = { from="database", key="POSTGRES_DB" }
# ...
SECRET_KEY = { type="string", random=true, length=24 }
```

Environment variables declared in the `nua-config` file can be changed when an instance is started. This feature allows both:

- Simplified deployment of an application for standard cases,
- Fine-tuning if needed, especially for the case of parallel deployment of several instances of the same application.

Some of these variables in the above example are *dynamic*. Nua's orchestrator establishes a gateway between the main application and an auxiliary resource (here a database service declared below, named "database"). Each directive allows a property of the resource to be assigned to a variable in the application environment (for example, the host address on the network, the name of the database, etc.). These dynamic variables allow other functionalities such as the automatic generation of names or passwords.

For applications that are not programmed to be configured via environment variables, a mechanism for generating config files, via a template language such as Jinja, is provided.

### `port` directive

This directive lists the ports to be configured by the orchestrator. Here a port named "web" is declared, and the application provides a service on port 3000. By default it is the `TCP` protocol, it will be routed later by the orchestrator to a domain name.

```toml
[port.web]
container = 3000
```

### `healthcheck` section

The `healthcheck` directive is used to declare a monitoring configuration for the application. Currently, it is a simple transcription of the `HEALTHCHECK` command from Docker, the underlying container format.

```toml
[healthcheck]
command = "node /nua/build/hedgedoc/healthcheck.mjs"
interval = 10
```

### List of `volume` directive

It is possible to declare storage spaces of different types. By default, the "volume" type is a space managed locally by the Docker server. Other volume types are available (`bind` for manually managed local resources, `tmpfs`, or any remote resource type which has a driver for Docker. The value of the `prefix` tag will be appended with the instance name (name of the domain served) to give the instance a unique volume name.

```toml
[[volume]]
type = "volume"
prefix = "hedgedoc_uploads"
target = "/hedgedoc/public/uploads"

[volume.backup]
method = "sync"
destination = "local"
frequency = "24h"
```

The volume can be accompanied by a backup directive. As with environment variables, these directives can be changed when deploying an instance. For example, a test or demo instance does not have the same backup requirements as a production instance.

### List of `resource` directive

Finally, the `resource` directive is used to declare a resource, i.e. an application or service. This can be a local or remote service, or in this case a container.

```toml
[[resource]]
name = "database"
type = "postgres"
version = ">=14, <15"

[resource.backup]
method = "pg_dumpall"
destination = "local"
frequency = "24h"
```

Here, this statement asks the orchestrator for a database container of type `Postgres version 14`. The name "database" is used earlier in the configuration to tell the application the characteristics of the created database (database name, password, etc). As with volumes, a backup directive can be specified.
