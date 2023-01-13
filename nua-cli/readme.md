Nua CLI
=======

Command-line interface for Nua.

Used by developers and devops people to deploy and manage applications.

## Usage

```bash
nua --help
# or
nua [command] [options]
```

## Commands (TBC)

- `deploy` - Deploy an application
- `list` - List deployed applications
- `destroy` - Destroy a deployed application
- `start` - Start an application
- `stop` - Stop an application
- `help` - Show help
- `version` - Show version
- `status` - Show Nua status
- `logs` - Show logs for an application
- `config` - Show configuration of a deployed application
- `update` - Update an application
- `backup` - Backup a deployed application
- `restore` - Restore backup data of a deployed application

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
