SCHEMA := $(wildcard fbtest/schema/*.fbs)
PYBINDS := $(patsubst %.fbs,%.py,$(SCHEMA))
TESTS := $(wildcard test_*.py)
.DEFAULT_GOAL := all

fbtest/schema/%.py: fbtest/schema/%.fbs
	flatc --python $<

pybinds: $(PYBINDS)

$(TESTS): pybinds
	pytest -sv $@

all: test
test: $(TESTS)

clean:
	rm fbtest/schema/*.py || true

.PHONY: $(TESTS)
