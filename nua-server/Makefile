PKG := nua_server
SRC := src

.PHONY: all
all: test lint


## Start development server
run:
	uvicorn nua_server.main:app --reload


#
# Testing
#
.PHONY: test test-with-coverage test-with-typeguard clean-tests

## run tests quickly with the default Python
test:
	@echo "--> Running Python tests"
	pytest --ff -x -p no:randomly
	@echo ""

test-with-coverage:
	@echo "--> Running Python tests (with coverage)"
	py.test --cov $(PKG)
	@echo ""

.PHONY: test-with-typeguard
test-with-typeguard:
	@echo "--> Running Python tests (with typeguard)"
	pytest --typeguard-packages=${PKG}
	@echo ""

## remove test and coverage artifacts
clean-test:
	rm -f .coverage
	rm -fr htmlcov/
	rm -fr .pytest_cache


#
# testing & checking
#
.PHONY: lint

## check style
lint:
	ruff check $(SRC) tests
	flake8 $(SRC) tests
	isort --check $(SRC) tests
	black --check $(SRC) tests
	# mypy $(SRC) tests
	# pyright
	# deptry .


#
# Formatting
#
.PHONY: format format-py

## format code
format: format-py

format-py:
	black $(SRC) tests
	isort $(SRC) tests


#
# Cleaning up
#
.PHONY: clean tidy

## cleanup
clean:
	find . -name __pycache__ -print0 | xargs -0 rm -rf
	find . -type d -empty -delete
	rm -rf .mypy_cache .pytest_cache .ruff_cache

## cleanup harder
tidy: clean
	rm -rf .tox .nox


#
# Update environment
#
update-env:
	poetry run pip install -U pip setuptools wheel poetry
