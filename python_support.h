#ifndef __PIET_PYTHON_SUPPORT_H__
#define __PIET_PYTHON_SUPPORT_H__

#include <Python.h>
#include <string>

struct python_object
{
	python_object();
	python_object(PyObject *obj_);
	~python_object() {}

	void incref() { Py_XINCREF(_obj); }
	void decref() { Py_XDECREF(_obj); }

	operator PyObject *() const { return _obj; }
	operator bool() const { return _obj!=NULL; }

	protected:
	PyObject *_obj;

	friend std::ostream &operator <<(std::ostream &os_, const python_object &ob_);
};

struct python_cmd
{
	python_cmd();
	python_cmd(const std::string &channel_, const std::string &cmd_, int paramcount_);
	python_cmd(const python_cmd &rhs_);
	~python_cmd();
	python_cmd &operator << (int i);
	python_cmd &operator << (const std::string &str_);
	void operator()();
	const python_cmd &operator =(const python_cmd &rhs_);

	private:

	void add_param(const python_object &ob);

	public:

	std::string _channel;
	std::string _cmd;
	python_object _args;
	int _size;
	int _index;
};
std::ostream &operator <<(std::ostream &os_, const python_cmd &pc_);

struct python_lock
{
	python_lock(const std::string &occasion_);
	~python_lock();

	static pthread_key_t _key;
	static void global_init();
	static void global_deinit();

	const std::string _occasion;
};

#endif // __PIET_PYTHON_SUPPORT_H__
