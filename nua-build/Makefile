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
	pytest --cov $(PKG) --cov-report term-missing
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
	ruff $(SRC) tests
	flake8 $(SRC) tests
	isort --skip tests/apps --check $(SRC) tests
	black --exclude tests/apps --check $(SRC) tests
	mypy --exclude tests/apps $(SRC) tests
	pyright
	# deptry .

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
	rm -rf .mypy_cache .pytest_cache .ruff_cache
	rm -rf ./tests/apps/*/build_dir ./tests/apps/*/mariadb-1.1.4
# 	rm -rf *.egg-info *.egg .coverage .eggs .cache .mypy_cache .pyre \
# 		.pytest_cache .pytest .DS_Store  docs/_build docs/cache docs/tmp \
# 		dist build pip-wheel-metadata junit-*.xml htmlcov coverage.xml

.PHONY: tidy
tidy: clean
	rm -rf .tox .nox

