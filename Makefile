PACKAGE=flatboobs


flake8:
	flake8 $(PACKAGE)

pylint:
	pylint --disable=fixme --rcfile=./pylintrc $(PACKAGE)

mypy:
	mypy --config-file ./mypy.ini $(PACKAGE)

syntax: flake8 pylint mypy


test:
	pytest -sv

coverage:
	pytest --cov-report term-missing --cov=flatboobs -sv tests/

clean:
	find $(PACKAGE) -type d -name __pycache__ -exec rm -rv {} +
	find tests -type d -name __pycache__ -exec rm -rv {} +
	rm -rv .eggs $(PACKAGE).egg-info || true
	rm -rv .mypy_cache .pytest_cache .coverage || true


all: syntax test

.PHONY: all flake8 pylint mypy test $(SUBDIRS)
