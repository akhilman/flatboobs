PACKAGE := flatboobs


flake8:
	flake8 $(PACKAGE)

pylint:
	pylint --disable=fixme --rcfile=./pylintrc $(PACKAGE)

mypy:
	mypy --config-file ./mypy.ini $(PACKAGE)

syntax: flake8 pylint mypy

inplace:
	python ./setup.py build_cmake --inplace

test: inplace
	make -C tests/acceptance pybinds
	pytest -sv tests

coverage:
	make -C tests/acceptance pybinds
	pytest --cov-report term-missing --cov=flatboobs -sv tests/

clean:
	rm -rv build || true
	rm -rv dist || true
	make -C tests/acceptance clean
	find $(PACKAGE) -type d -name __pycache__ -exec rm -rv {} +
	rm -rv __pycache__ || true
	find tests -type d -name __pycache__ -exec rm -rv {} +
	rm -rv .eggs $(PACKAGE).egg-info || true
	rm -rv .mypy_cache .pytest_cache .coverage || true
	rm -v flatboobs/*.so || true
	rm -rv flatboobs/include || true


all: syntax test

.PHONY: all flake8 pylint mypy test $(SUBDIRS)
