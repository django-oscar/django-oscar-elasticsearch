.PHONY: fail-if-no-virtualenv all install loaddata test

all: install migrate loaddata collectstatic


install: fail-if-no-virtualenv
	pip install --pre --editable .[dev,test] --upgrade --upgrade-strategy=eager

migrate:
	sandbox/manage.py migrate --no-input

collectstatic:
	sandbox/manage.py collectstatic --no-input

lint:
	black --check --exclude "migrations/*" setup.py oscar_elasticsearch
	pylint setup.py oscar_elasticsearch/

test:
	pip install --pre --editable .[test] --upgrade --upgrade-strategy=eager
	sandbox/manage.py test

black:
	black --exclude "migrations/*" setup.py oscar_elasticsearch

clean: ## Remove files not in source control
	find . -type f -name "*.pyc" -delete
	rm -rf nosetests.xml coverage.xml htmlcov *.egg-info *.pdf dist violations.txt

package: clean
	pip install --upgrade pip twine wheel
	rm -rf dist/
	rm -rf build/
	python setup.py clean --all
	python setup.py sdist bdist_wheel
