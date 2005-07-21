#ifndef __PIET_PYTHON_H__
#define __PIET_PYTHON_H__

#include <Python.h>
#include <string>
#include <list>

struct python_handler
{
	~python_handler();

	static python_handler &instance()
	{
		static python_handler handler;
		return handler;
	}

	void read(const std::string &channel_, const std::string &file_);

	void exec(const std::string &channel_, const std::string &code_);

	void cleanup();
	void killall();
	std::list<std::string> threadlist();
	
	void read_and_exec(
			const std::string &channel_,
			const std::string &file_,
			const std::string &cmd_);
	protected:
	python_handler();
	
	PyThreadState * _main_thread_state;
};

#endif // __PIET_PYTHON_H__
