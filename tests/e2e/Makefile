.PHONY: test clean format


test:
	./runtest.py -v

clean:
	vagrant destroy
	rm -rf .vagrant apps ssh-config Vagrantfile install.py


format:
	black *.py
	isort *.py
