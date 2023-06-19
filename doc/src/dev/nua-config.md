# Detailed `nua-config` format

## The `nua-config` file

For global explanation of usage of the nua-config file based on an example, read the document [configuration](./configuration.md).

This document aims to describe exhaustively the possible fields of a `nua-config` file. The nua-config file is intended to contain only a limited set of metadata, it is usefully supplemented with descriptive files (readme, changelog, info on the packager).

Last revision: `nua-build version 0.5.20`

The syntax used by default and through this document examples is the TOML language, but `nua-config` file can also be written with YAML and JSON formats.

## Sections:

The `nua-config` file contains several sections, mandatory or optional. Their order is not fixed (although we advise to keep a logical order).

#### `[metadata]`

- **Mandatory**
- Contains the information that describes the application. Metadata is used as a basis for naming images, volumes and providers.

#### `[build]`

- **Optional**
- Specifies the environment and, if applicable, the specific actions to be performed to build the executable artifact(s) of the application.
- Note: could be splitted or organized in future versions of nua-build into the various steps of a build sequence
- Note: optional, but most packages should provide a [build] information

#### `[run]`

- **Optional**.
- Contains the actions to perform to start the applications.
- Note: the `run` section can make use of runtime environment variables
- Note: optional, but most packages should provide a [run] information

#### `[env]`

- **Optional**.
- Environment variables, static or dynamic. The variables can be replaced by new values at runtime.

#### `[docker]`

- **Optional**.
- Options specific to run docker containers (Docker concepts using `pydocker` syntax).

#### `[port]`

- **Optional**. However, the current implementation issues a warning if no public port is declared.
- Dictionary of named ports (ie: `[port.web]`) used by the application. `port.web` is special: it is used by default for https redirection.

#### `[healthcheck]`

- **Optional**.
- Healthcheck options (Docker concepts using `pydocker` syntax).
- Note: implementation is a work in progress, currently using directly the Docker commands.

#### `[backup]`

- **Optional**.
- Parameters for the backup of the application container
- Note: implementation is a work in progress


#### `[[volume]]`

- **Optional**.
- List of volumes declarations, either local or remote.
- Note: each volume can have a backup sub section


#### `[[provider]]`

- **Optional**.
- List of containers or services required by the application. For example, declaration of a database.
- Note: each provider can have a backup sub section


## Section `metadata`

Notes:

- If not specified, the type of the value is String with no length limitation.
- String are Python `f-string`: use of `{}` to reference other Metadata (such as version) is possible.
- keys containing a '-' can also be written with a '_'.


#### `id`

- **Mandatory**
- Identifier of the package. Should be unique in the managed area.
- String (max 80 chars)
- The `id` is used to build package name.
- Example `id = "hedgedoc"`

#### `version`

- **Mandatory**
- Version of the packaged application
- String (max 80 chars)
- The `id` is used to build package name.
- Example `version = "1.9.7"`

#### `title`

- **Mandatory**
- Short title of the package
- Example `title = "HedgeDoc"`

#### `author`

- **Mandatory**
- Author of the packaged application
- Example `author = "HedgeDoc authors"`

#### `license`

- **Mandatory**
- License of the packaged application.
- License format will use a standardised format (maybe SPDX)
- Example `license = "AGPL-3.0 license"`

#### `tagline`

- **Optional**
- Short description of the application
- Example `tagline = "The best platform to write and share markdown"`

#### `website`

- **Optional**
- String containing a valid URL
- Reference website of the application
- Example `website = "https://hedgedoc.org/"`

#### `tags`

- **Optional**
- List of strings
- List of tags describing the application
- Example `tags = ["Markdown", "Documentation", "Collaboration"]`

#### `profile`

- **Optional**
- Usage profile (WIP)

#### `release`

- **Optional**
- Integer
- Release number of this nua-config file
- If present, the release number is used to form the name of the builded image

#### `base-image`

- **Optional**
- String containing a valid Docker Hub reference
- For packages using a docker base image, the reference of the image (currently Docker Hub reference)
- Example `base-image = "tuxgasy/dolibarr:{version}"`

#### `src-url`

- **Optional**
- String containing a valid URL
- URL of the source code of the application
- Example `src-url = "https://github.com/hedgedoc/hedgedoc/releases/download/{version}/hedgedoc-{version}.tar.gz"`

#### `src-checksum`

- **Optional**
- If provided, the checksum will be enforced upon the downloaded source code.
- Supported format: SHA256 only.
- Example `src-checksum = 'c9bd99c65cf45fa1d7808855b46abbfa13b24400254d8da5e81dae2965494bb3'`

#### `git-url`

- **Optional**
- String containing a valid URL
- If code source is in a git repository, URL of the repository
- Example `git-url = "https://github.com/jech/galene.git"`

#### `git-branch`

- **Optional**
- If using a git repository, the branch to check out.
- Example `git-branch = "galene-0.6-branch"`


## Section `build`

Notes:

- If not specified, the type of the value is String with no length limitation.
- All fields are optional

#### `method`
- Force selection of the build method, possible values are 'build' or 'wrap'
- If value is not set, default to 'build' or 'wrap' if a 'metadata/base-image' is found
- Used to force selection of the special 'wrap' method that convert an existing Dockerfile to a Nua compliant one by adding metadata to the Docker image. For a real case, see the `Dolibarr` sample application in the apps folder of Nua code source.
- Example `method = "wrap"`


#### `builder`

- String or dict of string (alternate syntax)
- Reference of a specific Nua image dedicated to a development environment. Currently available values are node version 14 or 16, ruby versions 2.7, 2.7.2, 3.1, 3.2.
- If not specified, default builder provides Python 3.10. Development environment can also be installed in the build command or as packages.
- Note: syntax may change in future versions
- Example `builder = "node-14"`
- Example of alternate syntax `builder =  {name = "ruby", version = "3.2" }`


#### `packages`

- String or list of string (alternate syntax)
- Ubuntu packages to install for the build step. These packages will be removed after the `build` stage (except if they are required for the `run`stage.)
- Example `packages = "build-essential"``
- Example `packages = ['golang-go', 'git']`


#### `meta-packages`

- String or list of string (alternate syntax)
- Group of packages defined by Nua to facilitate some installation.
- Currently, only `postgres-client` and `mariadb-client` are available, and both   should be automatically installed when the auto-detection algorithm detect the use of the relevant DB in the `[[provider]]` section. So this feature is seldom used.
- Note: functionality may evolve in future versions.
- Example `meta-packages = ["postgres-client"]`


#### `build`

- String or list of string (alternate syntax)
- string must contain sh code that will be executed as root in the Dockerfile environment.
- Important: if not present, an auto-detection algorithm will try to do the standard installation using project configuration (implemented for Python and NodeJs).
- If a `build.py` file is found in the `./nua` folder, it is executed
- Example of a do-nothing command `build = "true"`
- Example of a long command

```
build = [
    "CGO_ENABLED=0 go build -ldflags='-s -w'",
    "cp galene /nua/app",
    "cp LICENCE /nua/app",
    "cp -a static /nua/app",
    "mkdir /nua/app/groups",
    "mkdir /nua/app/data"
]
```

#### `test`

- String or list of strings, containing one or several a shell commands
- "Smoke test" to quickly check that the installation was successful, an exit code of zero expected.
- If not present a minima test does check that some Nua internal file is present in the container hierarchy.
- Example `test = "python -c 'import flask_show'"`

#### `pip-install`
- String or list of strings
- List of python packages to install with the pip command
- To be used for applications no providing a `requirement.txt` or other `poetry.lock` file, or to install some `wheel` files.
- Example `pip-install = ["*.whl"]`
- Example `pip-install = ["flask", "gunicorn"]`


#### `project`
- Relative path of the project to build from the downloaded source code.
- Used in the situation of complex code archive when the build command need to be run from a non standard place
- Default `project = "."`
- Example `project = "./alternate/src"`


## Section `run`

Notes:

- If not specified, the type of the value is String with no length limitation.
- All fields are optional.
- All command string can use the shell expansion to access to ENV variables available in the run context.


#### `packages`
- String or list of strings
- Ubuntu packages needed by the application.
- Example `packages = ["fontconfig", "fonts-noto"]`


#### `start`
- String or list of strings
- Shell command executed with `sh -c` in the container environment to start the application when the container is started.
- if the `start`field is not present, the builder looks for a `start.py` file in the `nua` folder.
- Example `start = "bundle exec rails s"``
- Example `start = "yarn start"`
- Example `start = ["init-db", "gunicorn --workers 2 -b :5000 flask_app.app:app"]``

- Example of a long command

```
start = """\
/nua/app/galene \
-insecure \
-http 127.0.0.1:${LISTEN_PORT} \
-turn :${TURN_PORT} \
-udp-range 49152-65535 \
-groups /nua/app/groups \
-data /nua/app/data"""
```


## Section `env`

Each field is a variable declaration. Format can be:

- a Python `f-string`,
- a dict using a from / key syntax to access to other values of the running environment,
- a dict using specific parameters for special functions like generating a password.

- Example simple values
```
NODE_ENV = "production"
DEBUG = "true"
UPLOADS_MODE = "0700"
TZ = "Europe/Paris"
```

Using a dict permits to copy a value from another section. The `from` field identifies the item id and the `key` field identifies the value to copy. If the `from` field is omitted, default ENV is used.

- Example to copy information from a DB declared in the `provider` section with name `database`. For a provider, a special environment variable is `hostname` which refers to the name of the relevant docker container in the local sub network.
```
DB_HOST = { from="database", key="hostname" }
DB_PORT = { from="database", key="POSTGRES_PORT" }
DB_NAME = { from="database", key="POSTGRES_DB" }
DB_USERNAME = { from="database", key="POSTGRES_USER" }
DB_PASSWORD = { from="database", key="POSTGRES_PASSWORD" }
```

- Example to copy the value of the app `domain` (fqdn) to the application at start time. `domain` field is relative to the current Docker environment so the reom kay is not necessary.
```
CMD_DOMAIN = { from="", key="domain" }
CMD_ALLOW_ORIGIN = { key="domain" }
```

- Example of the special function `random` to generate a password
```
GALENE_ADM_PWD = { random='true', length=24 }
```

- Example to generate a password, with an attribute asking to display the password
```
ACKEE_PASSWORD = { random='true', length=16, display='true' }
```

- Example of complex string using `f-string` evaluation
```
DB_HOST = { from="database", key="hostname" }
DB_USER = { from="database", key="MONGO_INITDB_ROOT_USERNAME" }
DB_PWD = { from="database", key="MONGO_INITDB_ROOT_PASSWORD" }
DB_PORT = 27017
ACKEE_MONGODB = "mongodb://{DB_USER}:{DB_PWD}@{DB_HOST}:{DB_PORT}/"
```

- Example of the special function `external_ip` to access to the detected external IP of the host (public IP)

```
MY_IP = { external_ip='true' }
```



## Section `docker`

Most application will not require any tuning in this section.
Each key/value pair of this section must be a valid py-docker parameter, see:
https://docker-py.readthedocs.io/en/stable/containers.html

Some values should no be used, because the orchestrator manage them directly, like fields related to volumes and mount points, healthcheck, ports.

By default, the nua-orchestrator uses these values:
- `detach = true`, this value is not editable
- `restart_policy.name = "always"`, restart always a crashed container, could be modified to custom configuration like `{"Name": "on-failure", "MaximumRetryCount": 5}`
- `mem_limit = 16M`, default memory limit for the container
- `auto_remove = false`, no auto-removal of the container on daemon side when the container’s process exits

A special value is the networking mode of the container. The `nua-orchestrator` expects that all containers are in sub networks. However, some rare applications may require to run in the actual host network. An example is the `galene` application. Then all ports configuration must be hand made.
- `network = "host"`  for very special cases


## Section `port`

Each element of this section must be declared with a name used as a key. The `web` key name is special and has default values (default to proxy port 443 or 80). Other ports declarations must provide the proxyed port (port seen from the outside).
keys for a port are:
- `container` : mandatory, port used by the application to publish its web data (in the container). Must be configured.
- `host` : optional, port used in local network. By default this port is chosen by the orchestrator and should not be defined by the configuration file.
- `proxy` : public port proxyed by `nginx`. For the `web` port its default is 443. For other declared port the `proxy` value must be configured.
- `protocol` : optional, one of `tcp` or `udp`, default to `tcp`.
- `ssl` : optional, one of `true` or `false`, default to `true` (if using `https` protocol for the published domain).


- Example of the most common configuration structure
```
[port.web]
container = 5000
```

- Example of a multiple port configuration
```
    [port.web]
    container = 8765

    [port.portb]
    container = 8764
    proxy = 8764

    [port.portc]
    container = 8763
    proxy = 8763
    ssl = false
```

- Example of complex configuration using ENV variables to force values
```
[port.web]
container = { key="LISTEN_PORT" }
host = { key="LISTEN_PORT" }
```


## Section `healthcheck`

Currently `healthcheck` uses the Docker family of parameters.

- Example using a command and interval
```
[healthcheck]
command = "node /nua/build/hedgedoc/healthcheck.mjs"
interval = 10
```


## Section `backup`

Work in progress.


## Section `volume`

Volumes can be either of 3 types
    - `managed`, using a driver, for example the Docker volume management, the default type
    - `directory`, using a directory local to the host, configured and managed by the user. It is equivalent to the Docker concept of `bind` volume,
    - `tmpfs`, using a volatile RAM disk.

- Parameters for `managed` type:
    - `driver`: name of the driver. By default the value is `docker`, to use the Docker's "local" volume driver.
    - `name`: for the `directory` type, path of the directory. For `managed` base name for the volume that will be completed with the container instance identification. The `tmpfs`type does not require a name.
    - `target`: is the path of the related folder inside the container.
    - `options`: optional dictionary of options specific to the driver.

    - Example with a Docker managed volume:

    ```
    [[volume]]
    # Mount source (e.g. a volume name or a host path):
    name = "hedgedoc-uploads"
    # Container path:
    target = "/hedgedoc/public/uploads"
    ```

    - Example with a remote `SSHFS` volume, using docker driver "sshfs"

    ```
    [[volume]]
    type = "managed"
    driver = "sshfs"
    name = "flask_uploads"
    target = "/var/tmp/uploads"
        [[volume.options]]
        sshcmd = "user@example.com:/var/test"
        # password = "testpassword"  # if password authentication
        IdentityFile= "/nua/some_private_key"
    ```

    - Example with a local directory

    ```
    [[volume]]
    type = "directory"
    name = "/var/nua/nua_test"
    target = "/var/tmp/mount_point"
    ```

    - Example of a `tmpfs` volume

    ```
    [[volume]]
    type = "tmpfs"
    target = "/var/lib/sample_www"
        [[volume.options]]
        tmpfs_size = "2G"
        tmpfs_mode = 1777
    ```


## Section `provider`

A provider is another container required by the main app container or a local service.
Several providers can be declared. The provider host will appear in the same sub network as the main container.

- Providers are identified by a `name` that permits reference to the provider in the `env` section.
- `type` field is a work in progress categorization. Currently it permits to select mostly databases.



- Example for Postgres database
```
[[provider]]
# Declaration of the required image for the resurce, here the official Postgresql image.
name = "database"
type = "postgres"
version = ">=14, <15"
    [provider.backup]
    method = "pg_dumpall"
    destination = "local"
    frequency = "24h"
```


- Example for MongoDB database
```
[[provider]]
# Declaration of the required image for the provider, here MongoDB.
name = "database"
type = "mongo"
version = ">=5, <6"
```


- Example for Redis database (cache configuration)
```
[[provider]]
# declaration of the required image for the provider: official Redis image
name = "database"
type = "redis-cache"
version = ">=7"
```
