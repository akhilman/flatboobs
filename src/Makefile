CPP:=g++
CFLAGS:=--std=c++17 -Wall -shared -fPIC -O2 -flto=thin

# python
SUFFIX:=$(shell python3-config --extension-suffix)
LIBS:=$(shell python3-config --libs)
INCLUDES:=$(shell python3-config --includes)

# pybind11
INCLUDES:=$(INCLUDES) -I../third_party/pybind11/include

# flatbuffers
INCLUDES:=$(INCLUDES) -I../third_party/flatbuffers/include
LIBS:=$(LIBS)-L../third_party/flatbuffers -lflatbuffers

# SRCS=$(wildcard *.cc)
SRCS:=\
	example.cc \
	idl.cc
PROGS:=$(patsubst %.cc,%$(SUFFIX),$(SRCS))

all: $(PROGS)

%$(SUFFIX): %.cc
	$(CPP) -o $@ $< $(CFLAGS) $(INCLUDES) $(LIBS)

clean:
	rm $(PROGS)
