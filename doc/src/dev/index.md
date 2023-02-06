## Vision

The main activity of the developer in the Nua system is to create / adapt / maintain packages.

The  `nua_build` python package is designed to facilitate this task

### Principles

-   Eventually different container formats will be available to deploy applications. The first format taken into account is a `Docker` image.

-   If the software configuration to be packaged is simple, then the configuration files and the overall packaging process must remain simple.

As a result, the application configuration should have reduced adhesion with the
chosen container format and rely on reasonable defaults.

The configuration is based on:

-   A `nua-config.toml` settings file.

-   Python scripts, at least a build script to constrtuct the package and a start script to start the application,

-   For Docker, a minimal `dockerfile` is proposed by default and can be used as is for many applications. Indeed the choice is made to use python as a priority for the configuration operations, which simplifies the `dockerfile` accordingly.

The `nua_buil` package provides utilities to help the packager:

-   `shell.py` contains wrappers of basic Unix commands like `cat` or `mkdir -p`.

-   `exec.py` contains wrappers above `os.execvpe`, for example `exec_as_nua()` or `exec_as_nua()`.

-   `actions.py` uses the two previous ones to carry out tasks like `apt_get_install()` or `pip_install()`

`nua_build` contains both the tools allowing the developer to package the application and a bootstrap which will be installed in the container.

### Some basic example

**_Please note  the format will change during the development phase, this is not a tutorial_**

Example of a \`nodejs-basic package, containing no real application but only the installation of Nodejs. The build directory containes only 3 files, whose one is empty.

#### File `nua-config.toml`

```toml
[metadata]
id = "nodejs-basic"
version = "1.6"
title = "Node.js JavaScript agent"
author = "Nodejs authors"
tagline = "Node.js JavaScript agent"
website = "https://nodejs.org/"
tags = ["javascript", "nodejs"]
licence = "MIT"
profile = ["generic"]
release = 1

[build]
```

The [build] tag is empty:

- by default, the files in the build directory will be used to build the package (a "manifest" tag could have been used).

- Other options take reasonable default values: by default we are looking for a build script named... `build.py`, a startup file named `start.py`, and we use the default dockerfile.

#### File `build.py`:

```python
from nua_build.actions import install_nodejs
from nua_build.nua_config import NuaConfig


def main():
    # note: the config file is not needed here,
    # the code to show how to load it:
    os.chdir("/nua/build")
    config = NuaConfig(".")

    install_nodejs()


main()
```

And finally the `start.py`file is empty (there is no application to start).

#### File `Dockerfile`

The Docker images are based on a "Nua" image containing the Nua base, this Nua image
is itself based on an Ubuntu distribution with python 3.10 installed.
Hence the default dockerfile that will be used:

```dockerfile
ARG nua_builder_tag
FROM ${nua_builder_tag}

# app build:
COPY . /nua/build
RUN app_builder

CMD ["python", "/nua/scripts/start.py"]
```

### `Nuad` command

Other commands will complete the nuad tool, today it only contains one command: "build".

```text
nuad --help
Usage: nuad [OPTIONS] COMMAND [ARGS]...

  Nua build CLI inferface.

Options:
  -V, --version         Show Nua version and exit.
  -v, --verbose         Write verbose output.
  --install-completion  Install completion for the current shell.
  --show-completion     Show completion for the current shell, to copy it or
                        customize the installation.
  --help                Show this message and exit.

Commands:
  build  Build Nua package from some 'nua-config.toml' file.
```
