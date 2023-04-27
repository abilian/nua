.PHONY: test clean format


test:
	./runtests.py -v

clean:
	vagrant destroy --force
	rm -rf .vagrant apps ssh-config Vagrantfile install.py


format:
	black *.py
	isort *.py
