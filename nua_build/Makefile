PKG := nua_build
SRC := nua_build

.PHONY: all
all: test lint

#
# Testing
#
.PHONY: test
test: ## run tests quickly with the default Python
	@echo "--> Running Python tests"
	pytest --ff -x -p no:randomly
	@echo ""

.PHONY: test-with-coverage
test-with-coverage:
	@echo "--> Running Python tests (with coverage)"
	py.test --cov $(PKG)
	@echo ""

.PHONY: test-with-typeguard
test-with-typeguard:
	@echo "--> Running Python tests (with typeguard)"
	pytest --typeguard-packages=${PKG}
	@echo ""

.PHONY: clean-tests
clean-test: ## remove test and coverage artifacts
	rm -f .coverage
	rm -fr htmlcov/
	rm -fr .pytest_cache

#
# testing & checking
#
.PHONY: lint
lint: ## check style
	flake8 $(SRC) tests
	isort $(SRC)/**/*.py tests/**/*.py
	black --check $(SRC) tests
	mypy $(SRC) tests

#
# Formatting
#
.PHONY: format
format: format-py

.PHONY: format-py
format-py:
	black nua_build tests
	isort nua_build tests

#
# Cleaning up
#
.PHONY: clean
clean:
	find . -name __pycache__ -print0 | xargs -0 rm -rf
	find . -type d -empty -delete
	rm -rf *.egg-info *.egg .coverage .eggs .cache .mypy_cache .pyre \
		.pytest_cache .pytest .DS_Store  docs/_build docs/cache docs/tmp \
		dist build pip-wheel-metadata junit-*.xml htmlcov coverage.xml

.PHONY: tidy
tidy: clean
	rm -rf .tox .nox

