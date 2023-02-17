# Using the Command Line Interface

In its first iterations, Nua provides only a Command Line Interface (CLI).

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
  debug    Debug commands
  deploy   Search, install and launch Nua image.
  reload   Rebuild config and restart apps.
  restore  Restore last successful deployment.
  search   Search Nua image.
  status   Status of orchestrator.
```

## The `nua` set of commands

The `nua` command is a CLI provided by the `nua-cli` package. It is intended to be used by a standard user of Nua.

Nua uses SSH public key authentication, then a secure channel to the orchestrator is established using the SSH protocol.

Here is a list of `nua` commands (some of them are not implemented yet):

```text
Usage: nua [OPTIONS] COMMAND [ARGS]...

  Nua CLI.

Options:
  -V, --version         Show Nua version and exit.
  --install-completion  Install completion for the current shell.
  --show-completion     Show completion for the current shell, to copy it or
                        customize the installation.
  --help                Show this message and exit.

Commands:
  apps     List applications.
  backup   Backup a deployed application.
  build    Build app but don't deploy it.
  config   Show/edit application config.
  deploy   Deploy an application.
  destroy  Destroy an application.
  help     Show help.
  logs     Show application logs.
  restore  Restore backup data of a deployed application.
  server   Manage the Nua server.
  start    Start an application.
  stop     Stop an application.
  update   Update an application.
  version  Show Nua version.
```
