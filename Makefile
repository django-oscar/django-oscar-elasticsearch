.PHONY: fail-if-no-virtualenv all install loaddata test

all: install migrate loaddata collectstatic

fail-if-no-virtualenv:
ifndef VIRTUAL_ENV # check for a virtualenv in development environment
ifndef PYENVPIPELINE_VIRTUALENV # check for jenkins pipeline virtualenv
$(error this makefile needs a virtualenv)
endif
endif


install: fail-if-no-virtualenv
	pip install --pre --editable .[dev] --upgrade --upgrade-strategy=eager

migrate:
	sandbox/manage.py migrate --no-input

collectstatic:
	sandbox/manage.py collectstatic --no-input

lint: fail-if-no-virtualenv
	pip install -e .[dev]
	black --check --exclude "migrations/*" setup.py oscar_elasticsearch
	pylint setup.py oscar_elasticsearch/

test: fail-if-no-virtualenv
	sandbox/manage.py test

black:
	black --exclude "migrations/*" setup.py oscar_elasticsearch