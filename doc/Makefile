.PHONY: all run build clean deploy pdf

TARGET:=root@bulma:/var/www/html/nua.rocks/

SRC:=$(wildcard src/**/*.md)


all: build

src/dev/orchestrator.md: ../nua_orchestrator_local/README.md
	cp ../nua_orchestrator_local/README.md src/dev/orchestrator.md

run: $(src)
	python ./scripts/gen-api.py
	mkdocs serve

serve: run

build: $(src)
	python ./scripts/gen-api.py
	mkdocs build
	cp -a src/.well-known site/
	cp -a assets/root/* site/

deploy: build
	rsync -e ssh -avz site/ $(TARGET)

clean:
	rm -rf site

pdf: $(src)
	ENABLE_PDF_EXPORT=1 mkdocs build
