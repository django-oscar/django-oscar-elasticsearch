.PHONY: fail-if-no-virtualenv all install loaddata test

all: install migrate loaddata collectstatic

fail-if-no-virtualenv:
ifndef VIRTUAL_ENV # check for a virtualenv in development environment
ifndef PYENVPIPELINE_VIRTUALENV # check for jenkins pipeline virtualenv
$(error this makefile needs a virtualenv)
endif
endif


install: fail-if-no-virtualenv
	pip install --pre --editable .[test] --upgrade --upgrade-strategy=eager

migrate:
	manage.py migrate --no-input

loaddata:
	# manage.py loaddata

collectstatic:
	manage.py collectstatic --no-input

lint: fail-if-no-virtualenv
	black --check --exclude "migrations/*" setup.py oscar_elasticsearch
	pylint setup.py oscar_elasticsearch/

test: fail-if-no-virtualenv
	@coverage run --source='oscar_elasticsearch' `which manage.py` test
	@coverage report
	@coverage xml
	@coverage html

black:
	@black --exclude "migrations/*" setup.py oscar_elasticsearch