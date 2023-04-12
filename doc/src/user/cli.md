# Using the Command Line Interface

In its first iterations, Nua provides only a Command Line Interface (CLI).

## The `nua` set of commands

The `nua` command is a CLI provided by the `nua-cli` package. It is intended to be used by a regular user of Nua, from the confort of their own computer.

### Installation

Nua-cli will be released soon on PyPI.

In the meantime, you can install it from the source repository:

```bash
pipx install --force "git+https://github.com/abilian/nua.git#subdirectory=nua-cli"
```

Alternatively, if you're hacking on nua-cli, you can install it in editable mode from your local clone:

```bash
pipx install --force -e path/to/nua/nua-cli
```

### Authentication

Nua currently uses SSH public key authentication, then a secure channel to the orchestrator is established using the SSH protocol.

This means you need SSH access to the `nua` account of the [orchestrator server](./install.md).


### `nua` commands

Here is a list of `nua` commands (some of them are not implemented yet):

```text
Nua CLI (0.5.7)

Usage:
  nua <command> [options] [arguments]

Options:
  -h  Show help and exit
  -V  Show version and exit
  -d  Enable debug mode
  -v  Increase verbosity

Available commands:
  apps             List applications.
  backup           Backup a deployed application.
  config           Show/edit application config.
  destroy          Destroy an application.
  help             Show help.
  logs             Show application logs.
  restart          Restart an application.
  restore          Restore backup data of a deployed application.
  server           Manage the Nua server.
  start            Start an application.
  stop             Stop an application.
  update           Update an application.

 config
  config show      Show application config.

 server
  server logs      Show server logs.
  server ps        List all server processes.
  server settings  Show server settings.
  server status    Show Nua status.
  server uptime    Show server uptime.
```


## Managing the orchestrator

These commands are not intended for a standard user of Nua.

Currently, the orchestrator, as a server, is managed using the following commands:

```text
$ nua-orchestrator --help
Usage: nua-orchestrator [OPTIONS] COMMAND [ARGS]...

  Nua orchestrator local.

Options:
  -V, --version         Show Nua version and exit.
  --install-completion  Install completion for the current shell.
  --show-completion     Show completion for the current shell, to copy it or
                        customize the installation.
  --help                Show this message and exit.

Commands:
  backup   Backup now all instance having a backup rules.
  config
  debug    Debug commands.
  deploy   Search, install and launch Nua image.
  reload   Rebuild config and restart apps.
  remove   Remove a deployed instance and all its data.
  restart  Restart a deployed instance.
  restore  Restore last successful deployment.
  search   Search Nua image.
  start    Start a deployed instance.
  status   Status of orchestrator.
  stop     Stop a deployed instance.
```
