
CC=g++
CXX=g++
TARGET_ARCH=-march=pentium2
CPPFLAGS=-I/home/weary/lubi
CXXFLAGS=-ggdb3 -Wall
LDFLAGS=-ggdb3

SOURCES=$(wildcard *.cpp)
OBJS:=$(patsubst %.cpp, %.o, $(SOURCES))
DEPS:=$(patsubst %.o,.%.d,$(OBJS))

LDLIBS=-ldl -llua -llualib -lcrypt -lpthread

all: .depend pietbot

pietbot: $(OBJS) /home/weary/lubi/lubi.a
	$(LINK.o) $^ $(LOADLIBES) $(LDLIBS) -o $@


-include $(DEPS)

.%.d: %.cpp
	@echo updating dependencies for $<
	@$(CC) -MD -E $(CPPFLAGS) $< > /dev/null
	@mv $(patsubst .%.d,%.d,$@) $@


.depend: $(DEPS)
	@touch .depend

