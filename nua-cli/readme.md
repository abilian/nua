# nua-cli: CLI for NUA (for users)

Command-line interface for Nua.

Used by developers and devops people to deploy and manage applications.

## Usage

```bash
nua --help
# or
nua [command] [options]
```

## Main commands

Here's the list of commands we should support, eventually (TBC):

```
apps              List apps
backup            Backup/restore app data
config            Show/manage config for current app
deploy            Deploy app
destroy           Destroy app
help              Display help
init              Create a new app
logs              Tail running logs
ps                Show process count
restart           Restart an app
run               Run a command in the app's environment
scale             Scale processes
start             Start an app
status            Show app status
stop              Stop an app
update            Update the Nua CLI
```

## Subcommands

+ additional commands for authentication, backup, etc.

Also, subcommands:

```
backup dump
backup restore

config show
config get
config set
config unset

system status
system ...

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
