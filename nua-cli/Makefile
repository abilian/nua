PKG := nua.cli
SRC := src/nua

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
	isort --check $(SRC) tests
	black --check $(SRC) tests
	mypy $(SRC) tests
	pyright $(SRC) tests
	deptry .

#
# Formatting
#
.PHONY: format
format: format-py

.PHONY: format-py
format-py:
	black $(SRC) tests
	isort $(SRC) tests

#
# Cleaning up
#
.PHONY: clean
clean:
	find . -name __pycache__ -print0 | xargs -0 rm -rf
	find . -type d -empty -delete
	rm -rf .mypy_cache .pytest_cache .ruff_cache

.PHONY: tidy
tidy: clean
	rm -rf .tox .nox


#
# Update environment
#
update-env:
	poetry run pip install -U pip setuptools wheel poetry
