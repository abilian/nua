.PHONY: test clean format


test:
	python -m e2e.runtests -v

clean:
	vagrant destroy --force
	rm -rf .vagrant apps ssh-config Vagrantfile install.py


format:
	black *.py
	isort *.py
