PACKAGENAME = flask_one_setup

all: nua

.PHONY: clean
clean:
	@rm -fr  build
	@rm -fr  build_dir
	@rm -fr  *.egg-info
	@rm -fr  *.whl

.PHONY: build
build:
	@rm -fr  build_dir
	@mkdir build_dir
	pip wheel .
	@cp $(PACKAGENAME)*.whl build_dir
	@cp nua-config.toml build.py start.py build_dir

.PHONY: nua
nua: build
	nua-build --verbose build_dir
