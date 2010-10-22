#ifndef __PIET_PYTHON_THREADING_H__
#define __PIET_PYTHON_THREADING_H__

#include <Python.h>
#include <boost/noncopyable.hpp>
#include <stdint.h>
#include <string>
#include <list>
#include <map>

namespace piet_py_intern
{
	struct py_thread_t;
	struct intern_lock_t;
}

typedef std::map<std::string,std::string> threadlocalmap_t;
threadlocalmap_t &getthreadlocalmap();

struct py_handler_t : public boost::noncopyable
{
	~py_handler_t() { if (!destructed) destruct(); }
	void destruct();

	static py_handler_t &instance();

	void read_file_if_changed(const std::string &channel_, const std::string &filename_);
	void exec(const std::string &channel_, const std::string &nick_, uint32_t auth_, const std::string &cmd_, const std::string &args_);

	std::list<std::string> threadlist() const;

protected:
	bool destructed;
	py_handler_t();
	void export_piet_funcs();
};

extern py_handler_t &g_python;


#endif // __PIET_PYTHON_THREADING_H__


