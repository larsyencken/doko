#
#  Makefile
#

default: test

env: requirements.txt
	test -d env || virtualenv env
	env/bin/pip install -r requirements.txt

env/bin/flake8: env
	env/bin/pip install flake8

lint: env/bin/flake8
	find doko -name '*.py' | xargs env/bin/flake8

test: lint
	env/bin/python -m unittest discover test
