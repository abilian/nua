# Nua

<img src="./doc/assets/logo.png" alt="logo nua">

[![codecov](https://codecov.io/github/abilian/nua/branch/main/graph/badge.svg?token=0PCZNVDRE8)](https://codecov.io/github/abilian/nua)

> **Warning**
> This code is currently highly experimental, and not meant for public consumption.
> We hope to have a usable, alpha or beta quality, release, by the end of Q1 2023.

## What is Nua?

### Vision

[Nua](https://nua.rocks/) is an open source, self-hosted cloud platform project (a PaaS - platform as a service).

Nua streamlines the development, selection, installation and resilient operation of web applications in a self-hosted cloud environment.

It is primarily aimed at users (SMEs, associations, public services, etc.) who wish to benefit from the simplicity of the cloud at the lowest cost without compromising the principles of digital sovereignty.

Its watchwords are: simplicity, resilience and equity.

### Concept Map

<img src="./doc/src/diagrams/mindmaps/Nua Concept Map.png" alt="concept map">

### Use cases

<img src="./doc/src/diagrams/others/Nua use cases.png" alt="use cases">

### Presentation

See: <https://speakerdeck.com/sfermigier/nua-a-self-hosted-resilient-paas>

----

## Hacking on Nua

### Technical Architecture

<img src="./doc/src/diagrams/c4/level1.png" alt="architecture">

### Subpackages

The Nua project is a monorepo, split into several subpackages:

- `nua-lib`: common code for all Nua packages ([details](./nua-lib/README.md)).
- `nua-cli`: command-line interface for Nua ([details](./nua-cli/README.md)).
- `nua-agent`: agent for Nua apps ([details](./nua-agent/README.md)).
- `nua-autobuild`: build Docker images used by Nua ([details](./nua-autobuild/README.md)).
- `nua-build`: build system for Nua packages ([details](./nua-build/README.md)).
- `nua-orchestrator`: orchestrator for Nua applications ([details](./nua-orchestrator/README.md)).
- `nua-server`: web UI for a Nua iserver ([details](./nua-server/README.md)). Not ready yet.

It also comprises several example applications, as well as a few real-world applications: [`apps`](./apps).

To install a development environment, you will need [Poetry](https://python-poetry.org/), and to run:

```
poetry install
```

You also need a Docker server.


### Roadmap and current status

The roadmap for the projet is kept up to date on [this kanban board](https://github.com/abilian/nua/projects/1).

As of 2023/02/08, we have a:

- The "builder" CLI that can build container images.
- The "orchestrator" CLI that can deploy and manage container images.
- We have started packaging some applications (HedgeDoc, Dolibarr, simple demos).
- Work has started on a common `nua` CLI:

```console
$ nua
nua (0.5.11)

Usage:
  nua <command> [options] [arguments]

Options:
  -h  Show help and exit
  -V  Show version and exit
  -d  Enable debug mode
  -v  Increase verbosity

Available commands:
  apps     List applications.
  backup   Backup a deployed application.
  build    Build app but don't deploy it.
  deploy   Deploy app.
  destroy  Destroy an application.
  help     Show help.
  logs     Show application logs.
  restart  Restart an application.
  restore  Restore backup data of a deployed application.
  start    Start an application.
  stop     Stop an application.
  update   Update an application.

 config
  config show      Show application config.

 env
  env set          Show application env variables.
  env show         Show application env variables.

 server
  server cleanup   Cleanup server (remove inactive docker images and containers).
  server logs      Show server logs.
  server ps        List all server processes.
  server settings  Show server settings.
  server status    Show Nua status.
  server uptime    Show server uptime.
```

### REUSE (licensing compliance)

Result of the `reuse lint` command invocation:

```
$ reuse lint
> * Bad licenses:
> * Deprecated licenses:
> * Licenses without file extension:
> * Missing licenses:
> * Unused licenses:
> * Used licenses: AGPL-3.0-only, CC-BY-4.0, MIT
> * Read errors: 0
> * Files with copyright information: 284 / 284
> * Files with license information: 284 / 284

> Congratulations! Your project is compliant with version 3.0 of the REUSE Specification :-)
```
