#ifndef __PIET_PYTHON_H__
#define __PIET_PYTHON_H__

#include "python_support.h"
#include <list>
#include <string>

struct python_handler
{
	~python_handler();

	static python_handler &instance()
	{
		static python_handler handler;
		return handler;
	}

	void read(const std::string &channel_, const std::string &file_);

	void exec(const std::string &channel_, const python_cmd &code_);

	void cleanup();
	void killall();
	std::list<std::string> threadlist();
	
	void read_and_exec(
			const std::string &channel_,
			const std::string &file_,
			const python_cmd &cmd_);
	protected:
	python_handler();
	
	PyThreadState * _main_thread_state;
};


#endif // __PIET_PYTHON_H__
