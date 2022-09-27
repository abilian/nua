PACKAGENAME = flask_one_wheel

all: clean build nua

.PHONY: clean
clean:
	@rm -fr  $(PACKAGENAME)/dist
	@rm -fr  build_dir

.PHONY: clean
build:
	poetry build -f wheel

.PHONY: build
nua: build
	@rm -fr  build_dir
	@mkdir build_dir
	@mv dist/*.whl build_dir
	@cp nua-config.toml build.py start.py build_dir
	nua-build --verbose build_dir
