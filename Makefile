
CC=g++
CXX=g++
CPPFLAGS=-I/usr/include/python2.7
CXXFLAGS=-MMD -march=native -ggdb3 -Wall
LDFLAGS=-ggdb3

SOURCES=$(filter-out test.cpp,$(wildcard *.cpp))
OBJS:=$(patsubst %.cpp, %.o, $(SOURCES))
DEPS:=$(patsubst %.o,%.d,$(OBJS))

LDLIBS=-ldl -lcrypt -lpthread -lpython2.7 -lsqlite3

all: pietbot

pietbot: $(OBJS)
	$(LINK.o) $^ $(LDLIBS) -o $@

-include $(wildcard *.d)

clean:
	@rm -fv $(OBJS) $(DEPS) *.pyc *.pyo pietbot

