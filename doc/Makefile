.PHONY: run build clean deploy pdf

TARGET:=root@bulma:/var/www/html/nua.rocks/

run:
	mkdocs serve

build:
	mkdocs build

deploy: build
	rsync -e ssh -avz site/ $(TARGET)

clean:
	rm -rf site

pdf:
	ENABLE_PDF_EXPORT=1 mkdocs build
