PACKAGENAME = flask_mariadb_wheel

all: nua

.PHONY: clean
clean:
	@rm -fr  $(PACKAGENAME)/dist
	@rm -fr  build_dir

.PHONY: build
build:
	@rm -fr  build_dir
	@mkdir build_dir
	poetry build -f wheel
	@mv dist/*.whl build_dir
	@cp nua-config.toml build.py start.py build_dir

.PHONY: nua
nua: build
	nua-build --verbose build_dir
