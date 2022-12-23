.PHONY: all default


PKG=nua

all: default
default: test lint


#
# Run
#
.PHONY: run
run:
	uvicorn --reload nua.server:app


#
# testing
#
test:
	pytest

test-with-typeguard:
	pytest -v --typeguard-packages=$(PKG)

test-with-timing:
	pytest --durations=10

test-with-coverage:
	pytest --tb=short --cov $(PKG) --cov-report term-missing .



#
# Linting
#
lint: lint-py lint-mypy

lint-py:
	@echo "--> Style and basic linting w/ flake8"
	@make flake8
	black --check src tests
	@echo ""

lint-mypy:
	@echo "--> Typeckecking w/ mypy"
	-mypy src tests
	@echo ""


#
# Janitorial
#
clean:
	find . -name "*.pyc" -delete
	find . -name .DS_Store -delete
	find . -name cache -type d -delete
	find . -type d -empty -delete
	rm -rf .mypy_cache .pytest_cache .ruff_cache
	rm -f migration.log
	rm -rf build dist
	rm -rf tests/data tests/integration/data
	rm -rf tmp tests/tmp tests/integration/tmp
	rm -rf cache tests/cache tests/integration/cache
	rm -rf *.egg .coverage
	rm -rf doc/_build
	rm -rf htmlcov junit-*.xml
	rm -f ./src/app/static/dist/js/* ./src/app/static/dist/css/*
	rm -f ./front/dist/static/js/* ./front/dist/static/css/*
	rm -rf apps/*/_build

format: format-py

format-py:
	black -t py38 src scripts
	isort src scripts

update-deps:
	poetry update
	poetry export > requirements.txt
