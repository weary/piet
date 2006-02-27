
CC=g++
CXX=g++
TARGET_ARCH=-march=pentium2
CPPFLAGS=-I/home/weary/lubi -I/usr/include/python2.4
CXXFLAGS=-ggdb3 -Wall
LDFLAGS=-ggdb3

SOURCES=$(filter-out test.cpp,$(wildcard *.cpp))
OBJS:=$(patsubst %.cpp, %.o, $(SOURCES))
DEPS:=$(patsubst %.o,.%.d,$(OBJS))

LDLIBS=-ldl -lcrypt -lpthread -lpython2.4 -lsqlite3

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

