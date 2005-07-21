
#include "python_handler.h"

void collect_garbage()
{
	python_handler::instance().cleanup();
}

void killall()
{
	python_handler::instance().killall();
}


