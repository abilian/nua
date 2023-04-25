.PHONY: test clean format


test:
	./runtests.py -v

clean:
	rm -rf .vagrant apps ssh-config Vagrantfile install.py
	vagrant --force destroy


format:
	black *.py
	isort *.py
