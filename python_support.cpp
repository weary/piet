#include "python_handler.h"
#include "python_support.h"
#include "sender.h"
#include "bot.h"
#include <string>
#include <sstream>
#include <iostream>
//#include <boost/lexical_cast.hpp>

namespace
{
void privmsg(const std::string &channel_, const std::string str_)
{
	send(":%s PRIVMSG %s :%s\n", g_config.get_nick().c_str(), channel_.c_str(), str_.c_str());
}

std::string obj2str(PyObject *obj)
{
	std::ostringstream str;
	if (!obj)
	{
		str << "NULL";
	}
	else if (PyTuple_Check(obj))
	{
		PyTupleObject *t=reinterpret_cast<PyTupleObject *>(obj);
		int n=t->ob_size;
		str << "tuple<" << n << ">";
		for (int m=0; m<n; ++m)
			str << (m==0?'(':',') << obj2str(t->ob_item[m]);
		str << ')';
	}
	else if (PyList_Check(obj))
	{
		PyListObject *t=reinterpret_cast<PyListObject *>(obj);
		int n=t->ob_size;
		str << "list<" << n << ">";
		for (int m=0; m<n; ++m)
			str << (m==0?'(':',') << obj2str(t->ob_item[m]);
		str << ')';
	}
	else if (PyString_Check(obj))
	{
		str << '\"' << PyString_AsString(obj) << '\"';
	}
	else if (PyInt_Check(obj))
	{
		str << PyInt_AsLong(obj);
	}
	else if (PyFunction_Check(obj))
	{
		PyFunctionObject *t=reinterpret_cast<PyFunctionObject *>(obj);
		str << "function<" << obj2str(t->func_name) << ">";
	}
	else if (PyTraceBack_Check(obj))
	{
		str << "obj-traceback";
	}
	else if (PyClass_Check(obj))
	{
		PyClassObject *t=reinterpret_cast<PyClassObject *>(obj);
		str << "class(" <<
			obj2str(t->cl_bases) << ", " <<
			obj2str(t->cl_dict) << ", " <<
			obj2str(t->cl_name) << ")";
	}
	else if (PyDict_Check(obj))
	{
		python_object keys=PyDict_Keys(obj);
		str << "dict(" << keys << ")";
	}
	else if (PyModule_Check(obj))
	{
		str << "module<" << PyModule_GetName(obj) << ">";
	}
	else
	{
		str << "obj<" << obj->ob_type->tp_name << ">";
	}

	if (obj)
		str << 'x' << obj->ob_refcnt;

	return str.str();
}
}

std::ostream &operator <<(std::ostream &os_, const python_object &ob_)
{
	os_ << obj2str(ob_._obj);
	return os_;
}

python_object::python_object() : _obj(NULL)
{}

python_object::python_object(PyObject *obj_) : _obj(obj_)
{
	assert(!_obj || obj_->ob_refcnt>0);
}

python_cmd::python_cmd()
{
	static std::string emptystring;
	python_cmd::python_cmd(emptystring, emptystring, 0);
}

python_cmd::python_cmd(const std::string &channel_, const std::string &cmd_, int paramcount_) :
	_channel(channel_), _cmd(cmd_), _args(NULL), _size(paramcount_), _index(0)//, _dbg_cmd(cmd_)
{
	python_handler::instance();
	if (paramcount_)
	{
		python_lock guard(__PRETTY_FUNCTION__);
		_args = python_object(PyTuple_New(paramcount_));
	}
}

python_cmd::python_cmd(const python_cmd &rhs_) :
	_channel(rhs_._channel), _cmd(rhs_._cmd), _args(rhs_._args), _size(rhs_._size), _index(rhs_._index)//, _dbg_cmd(rhs_._dbg_cmd.str())
{
	{
		python_lock guard(__PRETTY_FUNCTION__);
		_args.incref();
	}
}

python_cmd::~python_cmd()
{
	{
		python_lock guard(__PRETTY_FUNCTION__);
		_args.decref();
	}
}

const python_cmd &python_cmd::operator =(const python_cmd &rhs_)
{
	{
		python_lock guard(__PRETTY_FUNCTION__);
		_args.decref();
		_channel = rhs_._channel;
		_cmd = rhs_._cmd;
		_args = rhs_._args;
		_size = rhs_._size;
		_index = rhs_._index;
		_args.incref();
	}
	return *this;
}

void python_cmd::add_param(const python_object &ob_)
{
	assert(_index<_size);
	
	PyTuple_SetItem(_args, _index, ob_);
	++_index;
}

python_cmd &python_cmd::operator << (int i)
{
	assert(_size>0);
	
	{
		python_lock guard(__PRETTY_FUNCTION__);
		python_object obj(PyInt_FromLong(i));
		add_param(obj);
	}

	return *this;
}

python_cmd &python_cmd::operator << (const std::string &str_)
{
	assert(_size>0);
	{
		python_lock guard(__PRETTY_FUNCTION__);
		python_object obj(PyString_FromString(str_.c_str()));
		add_param(obj);
	}
	return *this;
}

void python_cmd::operator()()
{
	std::cout << "PY: exec(" << *this << ")\n";

	{
		python_lock guard(__PRETTY_FUNCTION__);
		assert(_index==_size);
		assert(!_cmd.empty());

		python_object dict(PyImport_GetModuleDict());
		python_object module(PyDict_GetItemString(dict, "__main__"));
		python_object moduledict(PyModule_GetDict(module));
		python_object func(PyDict_GetItemString(moduledict, _cmd.c_str()));
		assert(PyCallable_Check(func));
		func.incref();

		python_object retval(PyObject_CallObject(func, _args));
		if (retval)
			retval.decref();
		else
		{
			PyObject *type_o, *value_o, *traceback_o;
			PyErr_Fetch(&type_o, &value_o, &traceback_o);
			python_object type(type_o), value(value_o), traceback(traceback_o);
			std::cout << "PY: ERROR: " << value << "\nerror class: " << type << "\ntraceback: " << traceback << "\n";
			privmsg(_channel, "ACTION kijkt gestoord op en roept: "+obj2str(value)+ ", en gaat daarna weer verder\n");
		}

		func.decref();
	}
	std::cout << "PY: exec(" << *this << ") finished\n";
}

std::ostream &operator <<(std::ostream &os_, const python_cmd &pc_)
{
	os_ << pc_._cmd << "(" << pc_._args << ")";
	return os_;
}

python_lock::python_lock(const std::string &occasion_)
	//: _occasion(occasion_)
{
	int lockcount = (int)pthread_getspecific(_key);
	pthread_setspecific(_key, (void *)(lockcount+1));
	//std::cout << "PL: acquiring python lock for " << _occasion;
	//if (lockcount) std::cout << ", already had " << lockcount;
	//std::cout << ".\n" << std::flush;
	if (lockcount==0) PyEval_AcquireLock();
	//std::cout << "PL: acquired by " << _occasion << "\n" << std::flush;
}
python_lock::~python_lock()
{
	int lockcount = ((int)pthread_getspecific(_key)) - 1;
	pthread_setspecific(_key, (void *)(lockcount));
	//std::cout << "PL: releasing python lock for " << _occasion;
	//if (lockcount) std::cout << ", but still " << lockcount << " left, so no real release";
	//std::cout << ".\n" << std::flush;
	if (lockcount==0) PyEval_ReleaseLock();
	//std::cout << "PL: released for " << _occasion << "\n" << std::flush;
}

void python_lock::global_init()
{
	//std::cout << "PL: initialising python locks\n" << std::flush;
	assert(pthread_key_create(&_key, NULL)==0);
}

void python_lock::global_deinit()
{
	//std::cout << "PL: de-initialising python locks\n" << std::flush;
	pthread_key_delete(_key);
}

pthread_key_t python_lock::_key;

