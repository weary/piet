
CC=g++
CXX=g++
CPPFLAGS=-I/usr/include/python2.6
CXXFLAGS=-O3 -march=pentium2 -ggdb3 -Wall
LDFLAGS=-ggdb3

SOURCES=$(filter-out test.cpp,$(wildcard *.cpp))
OBJS:=$(patsubst %.cpp, %.o, $(SOURCES))
DEPS:=$(patsubst %.o,.%.d,$(OBJS))

LDLIBS=-ldl -lcrypt -lpthread -lpython2.6 -lsqlite3 -lboost_regex

all: .depend pietbot

pietbot: $(OBJS)
	$(LINK.o) $^ $(LOADLIBES) $(LDLIBS) -o $@

test: test.o

-include $(DEPS)

.%.d: %.cpp
	@echo updating dependencies for $<
	@$(CC) -MD -E $(CPPFLAGS) $< > /dev/null
	@mv $(patsubst .%.d,%.d,$@) $@


.depend: $(DEPS)
	@touch .depend

