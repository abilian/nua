# nua-cli: CLI for NUA (for users)

Command-line interface for Nua.

[Nua](https://nua.rocks/) is an open source, self-hosted cloud platform project (a PaaS - platform as a service).

Used by developers and devops people to deploy and manage applications.

## Installation

### From PyPI

On PyPI the package is called just `nua` (not `nua-cli`) as it is the main interface for Nua users.

```bash
pipx install nua
nua
```

### From source

In the meantime, you can install it from the source repository:

```bash
pipx install --force "git+https://github.com/abilian/nua.git#subdirectory=nua-cli"
```

Alternatively, if you're hacking on nua-cli, you can install it in editable mode from your local clone:

```bash
pipx install --force -e path/to/nua/nua-cli
```

## Usage

```bash
nua --help
# or
nua [command] [options]
```

## Main commands and subcommands

Here's the list of commands we should support, eventually (TBC):

```
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


## Generic options

- `--help` - Show help
- `--version` - Show version number

## Examples (TBC)

```bash
nua deploy --help
nua deploy --app-id appid --domain fqdn
nua deploy --app-id appid --domain fqdn --env SOMEVAR=value
nua deploy --app-id appid --domain fqdn --env SOMEVAR=value --env-file .env
nua deploy --app-id appid --domain fqdn --env SOMEVAR=value --env-file .env --config config-path
nua deploy --app-id hedgedoc-1.9.6-10 --domain hdoc.example.com --env NODE_ENV=production
```
