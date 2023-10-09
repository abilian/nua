# User documentation

## Demo

To get a feel of how to use Nua as a user (both for building packages and deploying them), we have set up a "demo" app and configuration [here](https://github.com/abilian/nua/tree/main/demo).

Here is a recording of the demo script:

[![asciicast](https://asciinema.org/a/572550.svg)](https://asciinema.org/a/572550)

## Installation

{%
   include-markdown "../snippets/support.md"
%}

### Quick start

### Server installation
To install Nua on a fresh Ubuntu 22.04 server, run:

```console
curl -L https://nua.rocks/install.py | sudo python3
```

!!! danger "Do not install Nua on a server were other services are running!"
    When installed, Nua "takes over" the server, and will potentially interfere with other services such as Docker and locally installed databases.

    The recommended configuration is therefore to use a dedicated server (or VM).

    We plan to support more flexible configurations in the future.


### Command Line Interface (CLI) installation

To install the Nua CLI, run:

```console
pipx install nua
# or
pip install --user nua
```

### Detailed instructions

See: [Installation](./install/)

## Command line interface (CLI)

The Nua CLI can be installed independently from the rest of the Nua platform.

- [Using the Command Line Interface (CLI)](./cli/)

Warning: some aspects of this CLI are still being worked out!

## Web interface

We're still working on the web UI. Stay tuned!
