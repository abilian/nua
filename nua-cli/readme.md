Nua CLI
=======

Command-line interface for Nua.

Used by developers and devops people to deploy and manage applications.

## Usage

```bash
nua [command] [options]
```

## Commands (TBC)

- `deploy` - Deploy an application
- `list` - List applications
- `destroy` - Destroy an application
- `start` - Start an application
- `stop` - Stop an application
- `update` - Update an application
- `logs` - Show logs for an application
- `help` - Show help
- `version` - Show version
- `config` - Show configuration
- `init` - Initialize a new application

## Generic options

- `--help` - Show help
- `--version` - Show version number

## Examples (TBC)

```bash
nua deploy --help
nua deploy --version
nua deploy --name my-app --image my-image
nua deploy --name my-app --image my-image --port 80
nua deploy --name my-app --image my-image --port 80 --env NODE_ENV=production
nua deploy --name my-app --image my-image --port 80 --env NODE_ENV=production --env PORT=80
nua deploy --name my-app --image my-image --port 80 --env NODE_ENV=production --env PORT=80 --env-file .env
nua deploy --name my-app --image my-image --port 80 --env NODE_ENV=production --env PORT=80 --env-file .env --volume /var/log:/var/log
nua deploy --name my-app --image my-image --port 80 --env NODE_ENV=production --env PORT=80 --env-file .env --volume /var/log:/var/log --volume /var/www:/var
```
