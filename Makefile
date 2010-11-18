
CC=g++
CXX=g++
CPPFLAGS=-I/usr/include/python2.6
CXXFLAGS=-MMD -O3 -march=native -ggdb3 -Wall
LDFLAGS=-ggdb3

SOURCES=$(filter-out test.cpp,$(wildcard *.cpp))
OBJS:=$(patsubst %.cpp, %.o, $(SOURCES))
DEPS:=$(patsubst %.o,%.d,$(OBJS))

LDLIBS=-ldl -lcrypt -lpthread -lpython2.6 -lsqlite3 -lboost_regex

all: pietbot

pietbot: $(OBJS)
	$(LINK.o) $^ $(LDLIBS) -o $@

-include $(wildcard *.d)

clean:
	@rm -fv $(OBJS) $(DEPS) *.pyc *.pyo pietbot

