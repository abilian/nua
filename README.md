# Nua

<img src="./doc/assets/logo.png" alt="logo nua">

## Vision

Nua streamlines the development, selection, installation and resilient operation of web applications in a self-hosted cloud environment.

It is primarily aimed at users (SMEs, associations, public services, etc.) who wish to benefit from the simplicity of the cloud at the lowest cost without compromising the principles of digital sovereignty.

Its watchwords are: simplicity, resilience and equity.

## Concept Map

<img src="./doc/src/diagrams/mindmaps/Nua Concept Map.png">

## Use cases

<img src="./doc/src/diagrams/others/Nua use cases.png">

## Technical Architecture

<img src="./doc/src/diagrams/c4/level1.png">

## Roadmap and current status

The roadmap for the projet is kept up to date on [this kanban board](https://github.com/abilian/nua/projects/1).

As of 2022/06/17, we have a "builder" CLI that can build and manage container images:

```
fermigier@c17 ~/nua (main)> nuad --help
Usage: nuad [OPTIONS] COMMAND [ARGS]...

  Nua build CLI inferface.

Options:
  -V, --version         Show Nua version and exit.
  -v, --verbose         Write verbose output.
  --install-completion  Install completion for the current shell.
  --show-completion     Show completion for the current shell, to copy it or
                        customize the installation.
  --help                Show this message and exit.

Commands:
  build              Build Nua package from some 'nua-config.toml' file.
  delete             Delete the docker build of an app.
  dump_all_settings  Dump all settings from DB (.json).
  dump_nua_settings  Dump Nua settings from DB (.toml).
  list               List local docker images of Nua packages.
  load_nua_settings  Load Nua settings from .toml file.

```

