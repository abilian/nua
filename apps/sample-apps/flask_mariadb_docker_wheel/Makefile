
all: nua

.PHONY: clean
clean:
	@rm -fr  dist
	@rm -fr  build_dir

.PHONY: build
build:
	@rm -fr  build_dir
	@mkdir build_dir
	poetry build -f wheel
	@mv dist/*.whl build_dir
	@cp -a nua build_dir

.PHONY: nua
nua: build
	nua-build -vv build_dir
