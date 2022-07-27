# Nua orchestrator, implemented as a daemon

# WIP: basis for next iteration development


## Development notes:

`nua_orchestrator/`, is build on top of a `jsonrpc` server, see `server.py`.

Main dependencies:

    zmq
    tinyrpc
    psutil
    sqlalchemy_serializer
    tomli
    sqlalchemy
    typer

To install:

    poetry install


Server commands are `start`, `stop`, `restart`, `status`:

```text
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
```

The `demo_orchestrator_zmq.py` in `demos/` script does a quick test on a SQLite database with just a `User` table.

## Principle of the server

-   A master server (unix daemon), which launches other sub-servers:

    -   a "sentinel" server just there to manage the server's .pid in the event of some trouble,
    -   a JSONRPC / ZeroMQ server for the commands to be executed (for now only database modification methods)
    -   we can imagine other services in the future (flask, cron, ...)
    -   we can imagine other commands than 'start/stop'

    `tinyrpc` module: it would allow to switch to other transport layers than ZMQ (http, wsgi) if necessary.

The interest of JSONRPC is that it the protocol is both simple and very manageable (scripts/web/local/remote...).

## Data model

`orchestrator/db/model`: this is a mini schema with the User table. Using SQLite for a beginning, and including the `nua_build` model

## Settings

`orchestrator/nua_defaults_settings.toml`: parameters file, to see what will remain there, where will be moved elsewhere (same as management in env variables, DB, ...)

Like `nua_build`, the configuration is stored in the DB, the .toml file is a bootstrap at first launch.

In dev, I put everything in `/tmp`.

```toml
[server]
    pid_file = "/tmp/nua/orchestrator.pid"
    exit_flag = "/tmp/nua/orchestrator_exiting.pid"
    log_file = "/tmp/nua_orchestrator.log"
    start_zmq_server = true
[zmq]
    address="127.0.0.1"
    port=5001
[db]
    backend="sqlite"
    url="sqlite:////tmp/nua.db"
```

## zmq_rpc_server.py

So it's the rpc server, it's very short, the methods can be grouped by class: cf `nua_methods.py`, with the `@public` decorator.

For now only test methods on a table, more complex methods will be needed of course (database + install scripts, ...)

One can imagine a dynamic loading of the methods available via `importlib`.

You still need to do the CLI wrapper to have the 'nua install xxx' commands passed to the rpc server.

## advantages / disadvantages

-   Doing a server architecture can seem cumbersome and expensive. But this architecture is actually quite simple and above all very modular.
-   We can talk about interesting protocols rather than inventing a grammar of shell scripts,
-   the modularity and the fairly basic python code => easier to hack and develop,
-   we can make a 100% python,
-   extend and maintain quite easily (remote, automations, tests, ...),
