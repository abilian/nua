.PHONY: all develop test lint clean doc format
.PHONY: clean clean-build clean-pyc clean-test coverage dist doc install lint lint/flake8

# The package name
PKG=nua


all: lint

#
# Setup
#
develop: install-deps activate-pre-commit configure-git

install-deps:
	@echo "--> Installing dependencies"
	pip install -U pip setuptools wheel
	poetry install

activate-pre-commit:
	@echo "--> Activating pre-commit hook"
	pre-commit install

configure-git:
	@echo "--> Configuring git"
	git config branch.autosetuprebase always


#
# testing & checking
#
test-all: test

test:
	@echo "--> Running Python tests"
	pytest --ff -x -p no:randomly
	@echo ""

test-randomly:
	@echo "--> Running Python tests in random order"

clean-test: ## remove test and coverage artifacts
	rm -fr .tox/
	rm -f .coverage
	rm -fr htmlcov/
	rm -fr .pytest_cache


#
# Linting
#
lint:
	invoke lint


#
# Formatting
#
format: format-py format-js

format-py:
	docformatter -i -r nua-*
	black nua-*/
	isort nua-*/


#
# Doc
#
.PHONY: doc doc-html doc-pdf

doc: doc-html doc-pdf

doc-html:
	cd doc && make build

doc-pdf:
	echo TODO


#
# Everything else
#
install:
	poetry install

clean:
	inv clean
	find . -name __pycache__ -print0 | xargs -0 rm -rf
	find . -type d -empty -delete
	rm -rf .mypy_cache .pytest_cache .ruff_cache
	rm -rf */.mypy_cache */.pytest_cache */.ruff_cache
	rm -f .coverage */.coverage
	rm -rf dist nua-*/dist
	rm -rf apps/*/*/build_dir
	# Remove more cruft
	rm -rf *.egg-info *.egg .eggs .cache .mypy_cache .pyre \
		.pytest_cache .pytest .DS_Store  docs/_build docs/cache docs/tmp \
		dist build pip-wheel-metadata junit-*.xml htmlcov coverage.xml

tidy: clean
	rm -rf .tox .nox */.nox */.tox

update-deps:
	pip install -U pip setuptools wheel
	poetry update
	poetry export -o requirements.txt

publish: clean
	git push --tags
	poetry build
	twine upload dist/*
