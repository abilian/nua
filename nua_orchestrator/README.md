# Nua orchestrator, implemented as a daemon

## Development notes:

In `nua_orchestrator/`, there is a `jsonrpc` server, see `server.py`.

main dependencies:

    pip install zmq
    pip install tinyrpc
    pip install psutil
    pip install sqlalchemy_serializer
    pip install toml
    pip install sqlalchemy

To start (and restart...) the server without the Typer CLI thing (for tests), it is possible to directly use is as a module:

    python -c 'import nua_orchestrator as o; o.restart()'

server commands are `start`, `stop`, `retard`, `status`

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

`orchestrator/model`: this is a mini schema with just the User table. Using SQLite for a beginning.

## Settings

`orchestrator/params.toml`: parameters file, to see what will remain there, where will be moved elsewhere (same as management in env variables, DB, ...)

In dev, I put everything in `/tmp`

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
