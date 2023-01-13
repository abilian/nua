Nua CLI
=======

Command-line interface for Nua.

Used by developers and devops people to deploy and manage applications on local nua
installation.

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
- `update` - Update an application
- `logs` - Show logs for an application
- `help` - Show help
- `version` - Show version
- `config` - Show configuration of a deployed application
- `backup` - Backup a deployed application
- `restore` - Restore backup data of a deployed application

## Generic options

- `--help` - Show help
- `--version` - Show version number

## Examples (TBC)

```bash
nua deploy --help
nua deploy --image my-image --domain fqdn
nua deploy --image my-image --domain fqdn
nua deploy --image my-image --domain fqdn --env NODE_ENV=production
nua deploy --image my-image --domain fqdn --env NODE_ENV=production --env-file .env
nua deploy --image my-image --domain fqdn --env NODE_ENV=production --env-file .env --config deploy-config
```
