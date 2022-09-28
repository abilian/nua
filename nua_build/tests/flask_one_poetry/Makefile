PACKAGENAME = flask_one_poetry

all: nua

.PHONY: clean
clean:
	@rm -fr  build_dir

.PHONY: build
build:
	@rm -fr  build_dir
	@mkdir build_dir
	@cp -a $(PACKAGENAME) build_dir
	@cp pyproject.toml poetry.lock build_dir
	@cp nua-config.toml build.py start.py build_dir

.PHONY: nua
nua: build
	nua-build --verbose build_dir
