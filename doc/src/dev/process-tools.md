# Development process and tools

The project is made of several packages, but live in a single repository (a "[monorepo](https://lab.abilian.com/Tech/Tools/Monorepos/)").

To start hacking on the project, you need [git](https://git-scm.com/) and [poetry](https://python-poetry.org/).

You will need also an instance of Docker, either locally or remotely (in which case you should set the `DOCKER_HOST` environment variable accordingly).


## Monorepo and virtual environments

The project is a monorepo, so you need to install all dependencies in a single virtual environment.

To start hacking on the project, you should mostly need to type:

```shell
poetry shell
poetry install
```

This single environment can be used to develop all packages (i.e. you don't need to activate a specific environment for each package).

But since all subpackages have different sets of dependencies, you can use [Nox](https://nox.thea.codes/en/stable/) to run lint and tests for each subpackage:


## Additional tools

### Makefile

We provide a Makefile to ease some common tasks. Type `make help` to get a list of the most useful available targets.

### Abilian DevTools

Nua uses [Abilian DevTools](https://pypi.org/project/abilian-devtools/) to manage its QA process.
