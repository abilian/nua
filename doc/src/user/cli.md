# Using the Command Line Interface

In addition to the web interface, Nua has a Command Line Interface.
This CLI will provide both functionalities present in the web interface and specific functionalities

For the moment, each package defines a few commands, and a specific `nua_cli` provide some common fontend. these can be reorganized during development.

## Building packages

The only build environment command:

    nuad build

## Managing the orchestrator

These commands are not intended for a standard user of Nua.

Currently, the orchestrator, as a server, is managed using the following commands:

    $ nua-orchestrator --help
    Usage: nua-orchestrator [OPTIONS] COMMAND [ARGS]...

      Nua orchestrator server.

    Options:
      -V, --version         Show Nua version and exit.
      --install-completion  Install completion for the current shell.
      --show-completion     Show completion for the current shell, to copy it or
                            customize the installation.
      --help                Show this message and exit.

    Commands:
      restart  Restart orchestrator server.
      start    Start orchestrator server.
      status   Status of orchestrator server.
      stop     Stop orchestrator server.

## The `nua_cli` set of commands

When the orchestrator is started, it should provide both a web interface and a CLI interface.
The `nua_cli` CLI will be accessible

-   locally, permitting to the owner of the Nua instance to interact directly on the orchestrator.
-   remotely, permitting to identified users to perform a subset of these tasks.

Indeed dependending of the technical circumstance or technical culture of Nua users, some tasks
may be simpler to do from a CLI. For exempmple, dowloading some data into a file or moving containers between several hosts.

The local CLI is supported by a small RPC server on top of ZeroMQ. For remote access, Nua uses SSH public
 key authentication, then a secure channel to the local RPC server.

Some example of `nua_cli` task, administration of users:

    nua users --help
    Usage: nua users [OPTIONS] COMMAND [ARGS]...

    Options:
      --help  Show this message and exit.

    Commands:
      add     Add user account.
      count   Number or users in the table.
      delete  Delete users accounts.
      list    List users accounts.
      pubkey  Update some user account public key.
      update  Update some user account for one key/value pair.
