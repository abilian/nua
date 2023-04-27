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

```shell
nox -e lint
nox -e test
# Or just
nox
```

## Testing and static analysis

### Unit tests

You can run unit tests with:

```shell
make test
```

or:

```shell
nox -e test
```

### End-to-end tests (e2e)

We also provide a script to run the end-to-end tests, which are located in the `tests/e2e` directory.

These tests leverage a virtual machine managed by Vagrant, to start from a clean state each time. They take quite a bit of time, though.

You can run them with either:

```shell
make test-e2e
```

from the top level directory, or:

```shell
make
```

from the `tests/e2e` directory.


### Static analysis

We leverage several Python tools to perform static analysis:

- Ruff
- Flake8
- Mypy
- Pyright
- Bandit
- Safety
- Deptry
- Vulture

Each tool is configured in the `pyproject.toml` file or `setup.cfg` file of each package, or from the top level `pyproject.toml` file.

You can run all static analysis tools with:

```shell
nox -e lint
```

or:

```shell
make lint
```


## Additional tools

### Makefile and Invoke

We provide a Makefile to ease some common tasks. Type `make help` to get a list of the most useful available targets.

For a few complex tasks, we also provide a `tasks.py` file, which can be used with [Invoke](https://www.pyinvoke.org/). Type `invoke --list` (or `inv -l`) to get a list of the available tasks.

### Abilian DevTools

Nua uses [Abilian DevTools](https://pypi.org/project/abilian-devtools/) to manage its QA process.

## Release process

To release a new version on PyPI:

1. Run `invoke bump-version` from the main branch. (`invoke bump-version minor` for a minor release, `invoke bump-version major` for a major release)

2. Commit the changes, and push them to the main branch.

3. Run `invoke release`. This will, among other things:

    - Merge the main branch into the release branch.
    - Replace relative packages paths with PyPI package names.
    - Replace `nua-cli` by `nua`
    - Apply the proper tag
    - Build and publish the package on PyPI.
    - Build and publish the documentation on GitHub Pages.

The `main` -> `release` merge may fail. In this case, fix the conflicts, commit and push the changes, checkout `main` again then run `invoke release` again. This should work eventually.
