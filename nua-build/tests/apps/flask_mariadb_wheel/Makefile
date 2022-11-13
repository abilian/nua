PACKAGENAME = flask_mariadb_wheel

all: nua

.PHONY: clean
clean:
	@rm -fr  dist
	@rm -fr  build_dir

.PHONY: maria
maria:
	rm -fr mariadb-1.1.4
	unzip mariadb-1.1.4.zip
	cd mariadb-1.1.4 && python setup.py bdist_wheel
	mv mariadb-1.1.4/dist/*.whl .

.PHONY: build
build: maria
	@rm -fr  build_dir
	@mkdir build_dir
	poetry build -f wheel
	@mv dist/*.whl build_dir
	@mv *.whl build_dir
	@cp nua-config.toml build.py start.py build_dir

.PHONY: nua
nua: build
	nua-build --verbose build_dir
