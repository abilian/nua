# Detailed `nua-config` format

## The `nua-config` file

For global explanation of usage of the nua-config file based on an example, read the document [configuration](./configuration.md).

This document aims to describe exhaustively the possible fields of a `nua-config` file.

Last revision: `nua-build version 0.5.17`

The syntax used by default and through this document examples is the TOML language, but `nua-config` file can also be written with YAML and JSON formats.


## Sections:
The `nua-config` file contains several sections, mandatory or optional. Their order is not fixed (although we advise to keep a logical order).

#### `[metadata]`

- **Mandatory**
- Contains the information that describes the application. Metadata is used as a basis for naming images, volumes and resources.

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

- **Optional**. However the current implementation issues a warning if no public port is declared.
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



#### `[[resource]]`

- **Optional**.
- List of containers or services required by the application. For example, declaration of a database.
- Note: each resource can have a backup sub section


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
- example `id = "hedgedoc"`

#### `version`
- **Mandatory**
- Version of the packaged application
- String (max 80 chars)
- The `id` is used to build package name.
- example `version = "1.9.7"`

#### `title`
- **Mandatory**
- Short title of the package
- example `title = "HedgeDoc"`

#### `author`
- **Mandatory**
- Author of the packaged application
- example `author = "HedgeDoc authors"`

#### `license`
- **Mandatory**
- License of the packaged application.
- example `license = "AGPL-3.0 license"`

#### `tagline`
- **Optional**
- Short description of the application
- example `tagline = "The best platform to write and share markdown"`

#### `website`
- **Optional**
- String containing a valid URL
- Reference website of the application
- example `website = "https://hedgedoc.org/"`

#### `tags`
- **Optional**
- List of strings
- List of tags describing the application
- example `tags = ["Markdown", "Documentation", "Collaboration"]`

#### `profile`
- **Optional**
- Usage profile (WIP)

#### `changelog`
- **Optional**
- List of changes in the package

#### `name`
- **Optional**
- String to display as replacement of the `id` field
- Note: may be deprecated in future versions


#### `image`
- **Optional**
- String containing a valid Docker Hub reference
- For packages using a docker base image, the reference of the image (currently Docker Hub reference)
- example `image = "tuxgasy/dolibarr:{version}"`


#### `src-url`
- **Optional**
- String containing a valid URL
- URL of the source code of the application
- example `src-url = "https://github.com/hedgedoc/hedgedoc/releases/download/{version}/hedgedoc-{version}.tar.gz"`


#### `checksum`
- **Optional**
- If provided, the checksum will be enforced upon the downloaded source code.
- Supported format: SHA256 only.
- example `checksum = 'c9bd99c65cf45fa1d7808855b46abbfa13b24400254d8da5e81dae2965494bb3'`


#### `git-url`
- **Optional**
- String containing a valid URL
- If code source is in a git repository, URL of the repository
- example `git-url = "https://github.com/jech/galene.git"`


#### `git-branch`
- **Optional**
- If using a git repository, the branch to check out.
- example `git-branch = "galene-0.6-branch"`




## Section `build`

Notes:

- If not specified, the type of the value is String with no length limitation.
- All fields are optional


#### `builder`
- String or dict of string (alternate syntax)
- Reference of a specific Nua image dedicated to a development environment. Currently available values are node version 14 or 16, ruby versions 2.7, 2.7.2, 3.1, 3.2.
- If not specified, default builder provides Python 3.10. Development environment can also be installed in the build command or as packages.
- Note: syntax may change in future versions
- example `builder = "node-14"`
- example of alternate syntax `builder =  {name = "ruby", version = "3.2" }`


#### `packages`
- String or dict of string (alternate syntax)
- Ubuntu packages to install for the build step. These packages will be removed after the `build` stage (except if they are required for the `run`stage.)
- example `packages = "build-essential"``
- example `packages = ['golang-go', 'git']`


#### `meta-packages`
- String or dict of string (alternate syntax)
- Group of packages defined by Nua to facilitate some installation.
- Currently, only `postgres-client` and `mariadb-client` are available, and both   should be automatically installed when the auto-detection algorithm detect the use of the relevant DB in the `[[resource]]` section. So this feature is seldom used.
- Note: functionality may evolve in future versions.
- example `meta-packages = ["postgres-client"]`


#### `build-command`
- String or dict of string (alternate syntax)
- string must contains sh code that will be executed as root in the Dockerfile environment.
- Important: if not present, an auto-detection algorithm will try to do the standard installation using project configuration (implemented for Python and NodeJs).
- If a `build.py` file is found in the `./nua` folder, it is executed
- example of a do-nothing command `build-command = "true"`
- example of a long command

```
build-command = [
    "CGO_ENABLED=0 go build -ldflags='-s -w'",
    "cp galene /nua/app",
    "cp LICENCE /nua/app",
    "cp -a static /nua/app",
    "mkdir /nua/app/groups",
    "mkdir /nua/app/data"
]
```

#### `test`
- String, a shell command
- "Smoke test" to quickly check that the installation was successful, an exit code of zero expected.
- If not present a minima test does check that some Nua internal file is present in the container hierarchy.
- example `test = "python -c 'import flask_show'"`


#### `pip-install`
#### `method`
#### `project`
#### `document_root`
#### `nua_dir`


method = "wrap"
project = "."
document_root = "/nua/app/html"
nua_dir = "nua_files"
test = "python -c 'import flask_show'"
pip-install = ["*.whl"]
pip-install = ["flask", "gunicorn"]
