all: nua

.PHONY: clean
clean:
	@rm -fr dist

.PHONY: build
build:
	@rm -fr build_dir
	@mkdir -p build_dir
	poetry build -f wheel
	@mv dist/*.whl build_dir
	@cp nua-config.toml start.py build_dir

.PHONY: nua
nua: build
	nua-build -vv build_dir
