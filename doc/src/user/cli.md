# Using the Command Line Interface

In its first iterations, Nua provides only a Command Line Interface (CLI).

## The `nua` set of commands

The `nua` command is a CLI provided by the `nua-cli` package. It is intended to be used by a regular user of Nua, from the confort of their own computer.


### Installation

#### From PyPI

On PyPI the package is called just `nua` (not `nua-cli`) as it is the main interface for Nua users.

```bash
pipx install nua
nua
```

#### From source

When developing nua-cli, you can install it from the source repository:
```bash
pipx install --force "git+https://github.com/abilian/nua.git#subdirectory=nua-cli"
```

Or, in editable mode, from your local clone:
```bash
pipx install --force -e path/to/nua/nua-cli
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
