
#include "piet_py_handler.h"
#include "sender.h"
#include "privmsg_and_log.h"
#include "bot.h"
#include "piet_db.h"
#include <boost/lexical_cast.hpp>
#include <boost/scope_exit.hpp>
#include <iostream>
#include <stdexcept>
#include <map>
#include <signal.h>
#include <mutex>
#include <thread>
#include <pythread.h>

std::string pyunicode_asstring(PyObject *unicode)
{
	Py_ssize_t size = 0;
	const char *s = PyUnicode_AsUTF8AndSize(
			unicode, &size);
	if (!s)
		throw std::runtime_error("unicode string is not a unicode string");
	return std::string(s, size);
}

struct GILstate_ensure_t
{
	GILstate_ensure_t() :
		d_gstate(PyGILState_Ensure())
	{}

	~GILstate_ensure_t()
	{
		PyGILState_Release(d_gstate);
	}

protected:
	PyGILState_STATE d_gstate;
};

namespace piet_py_intern
{

static thread_local std::map<std::string, std::string> t_threadlocalmap;

// protects threadslist and modification map
static std::mutex g_mutex;
typedef std::list<piet_py_intern::py_thread_t *> threadlist_t;
static threadlist_t g_threads;

typedef std::map<std::string, time_t> modification_map_t;
static modification_map_t g_modification_map;

static PyThreadState *g_main_thread_state = NULL;


std::string py_repr(PyObject *obj_)
{
	if (!obj_) return "NULLrepr";
	PyObject *s = PyObject_Repr(obj_);
	std::string r = pyunicode_asstring(s);
	Py_XDECREF(s);
	return r;
}
std::string py_str(PyObject *obj_)
{
	if (!obj_) return "NULLstr";
	PyObject *s = PyObject_Str(obj_);
	std::string r = pyunicode_asstring(s);
	Py_XDECREF(s);
	return r;
}

void print_traceback(PyObject *tb_)
{
	assert(PyTraceBack_Check(tb_));

	PyObject *pystdout = PySys_GetObject("stdout");
	if (!pystdout)
	{
		threadlog() << "Cannot print traceback, sys.stdout not found\n";
		return;
	}
	threadlog() << "Writing traceback\n";
	PyTraceBack_Print(tb_, pystdout);
}

typedef std::lock_guard<std::mutex> lock_guard_t;


std::string mystrerror(int errnum)
{
	char buf[1024];
	const char *result = strerror_r(errnum, buf, 1024);
	if (!result)
	{
		snprintf(buf, 1024, "unknown error code %d", errnum);
		result = buf;
	}
	return result;
}


void *py_thread_t_run(void *self);

struct py_thread_t
{
	py_thread_t(
			const std::string &channel_, const std::string &nick_,
			uint32_t auth_, const std::string &cmd_, const std::string &args_) :
		d_thread_id(0),
		d_channel(channel_), d_nick(nick_), d_auth(auth_), d_cmd(cmd_),
		d_args(args_), d_our_tid(g_count++)
	{
		lock_guard_t guard(g_mutex);

		d_thread = std::thread([this](){this->run();});

		g_threads.push_back(this);

		d_thread.detach();
	}
	~py_thread_t()
	{
		lock_guard_t guard(g_mutex);
		g_threads.remove(this);
	}

	void run();

	long thread_id() const { return d_thread_id; };

	std::string str() const { return "[" + to_str(d_our_tid) + ": " + d_cmd + "(" + d_args + ")]"; }

protected:
	std::thread d_thread;
	long d_thread_id;  // python thread id
	std::string d_channel;
	std::string d_nick;
	uint32_t d_auth;
	std::string d_cmd;
	std::string d_args;
	uint32_t d_our_tid;  // our thread id
	static uint32_t g_count;
};
uint32_t py_thread_t::g_count = 0;

struct terminate_thread_exception_t : public std::exception
{
	const char *what() const throw() { return "terminate"; }
};



} // end namespace piet_py_intern
using namespace piet_py_intern;

// make sure the threading is initialised early
py_handler_t &g_python = py_handler_t::instance();

py_handler_t::py_handler_t() : d_destructed(false)
{
	printf("py_handler_t initialiser\n");

	t_threadlocalmap["tid"] = "main";
	t_threadlocalmap["nick"] = "system";
	t_threadlocalmap["auth"] = "0";

	export_piet_funcs();

	Py_Initialize();
	PyEval_InitThreads();

	g_main_thread_state = PyThreadState_Get();
	assert(PyGILState_Check());

	// release GIL
	d_initial_threadstate = PyEval_SaveThread();
}

void py_handler_t::destruct()
{
	if (d_destructed) return;
	d_destructed = true;

	PyEval_RestoreThread(d_initial_threadstate);  // re-acquire GIL

	threadlog() << "python handler destructed, cleaning up threads";
	{
		lock_guard_t guard(g_mutex);
		for(auto &thread: g_threads)
		{
			PyThreadState_SetAsyncExc(thread->thread_id(),
					PyExc_SystemExit);
		}

		PyThreadState *_save; _save = PyEval_SaveThread();
		while (1) // wait until threads actually finished
	 	{
			{
				lock_guard_t guard(g_mutex);
				if (g_threads.empty())
					break;
			}
			usleep(100);
		}
		PyEval_RestoreThread(_save);
	}

	assert(PyGILState_Check());
	Py_Finalize();
}


py_handler_t &py_handler_t::py_handler_t::instance()
{
	static py_handler_t instance;
	return instance;
}

void py_handler_t::read_file_if_changed(const std::string &channel_, const std::string &filename_)
{
	assert(!d_destructed);
	struct stat st;
	int r=stat(filename_.c_str(), &st);
	if (r!=0)
	{
		int e = errno;
		privmsg(channel_) << "Ik kan \"" << filename_ << "\" niet bereiken! (" << mystrerror(e) << ")";
	}
	else
	{
		std::unique_lock<std::mutex> guard1(g_mutex);
		modification_map_t::iterator i = g_modification_map.find(filename_);
		bool readit=false;
		if (i == g_modification_map.end())
		{ // new file, just read, no message
			readit=true;
		}
		else if (i->second!=st.st_mtime)
		{
			privmsg(channel_) << "ho! eerst de geweldige nieuwe " << filename_ << " lezen";
			readit=true;
		}

		if (readit)
		{
			g_modification_map[filename_]=st.st_mtime;
			guard1.unlock();

			threadlog() << "PY: reading file \"" << filename_ << '\"';
			FILE *f=fopen(filename_.c_str(), "r");
			if (!f)
				privmsg(channel_) << "ik kan " << filename_ << " niet openen!";
			else
			{
				GILstate_ensure_t gs;

				PyRun_SimpleFile(f, filename_.c_str());
				fclose(f);
			}
		}
	}
}


void py_handler_t::exec(const std::string &channel_, const std::string &nick_, uint32_t auth_, const std::string &cmd_, const std::string &args_)
{
	assert(!d_destructed);
	try
	{
		new py_thread_t(channel_, nick_, auth_, cmd_, args_);
	}
	catch(const std::exception &e)
	{
		threadlog() << "ERROR: " << e.what();
	}
}

std::list<std::string> py_handler_t::threadlist() const
{
	std::list<std::string> result;
	lock_guard_t guard(g_mutex);
	for (threadlist_t::const_iterator i = g_threads.begin(); i!=g_threads.end(); ++i)
		result.push_back((*i)->str());
	return result;
};

threadlocalmap_t &getthreadlocalmap()
{
	return t_threadlocalmap;
}

void py_thread_t::run()
{
	threadlocalmap_t &locmap = getthreadlocalmap();
	locmap["tid"] = to_str(d_our_tid);
	threadlog() << "thread started for " << d_cmd << "\n";
	{
		GILstate_ensure_t gs;

		d_thread_id = PyThread_get_thread_ident();
		assert(d_thread_id != 0);

		try
		{
			PyObject *func =
				PyDict_GetItemString(
						PyModule_GetDict(
							PyDict_GetItemString(
								PyImport_GetModuleDict(), "__main__")),
						d_cmd.c_str()); // borrowed ref
			if (!func || !PyCallable_Check(func))
				throw std::runtime_error((d_cmd + " not found or not callable").c_str());

			Py_XINCREF(func);

			PyObject *args = PyTuple_New(4);
			PyTuple_SetItem(args, 0, PyUnicode_FromStringAndSize(d_channel.data(), d_channel.size()));
			PyTuple_SetItem(args, 1, PyUnicode_FromStringAndSize(d_nick.data(), d_nick.size()));
			PyTuple_SetItem(args, 2, PyLong_FromLong(d_auth));
			PyTuple_SetItem(args, 3, PyUnicode_FromStringAndSize(d_args.data(), d_args.size()));
			locmap["channel"] = d_channel;
			locmap["nick"] = d_channel;
			locmap["auth"] = to_str(d_auth);
			locmap["cmd"] = d_cmd;
			locmap["args"] = d_args;

			PyObject *retval = PyObject_CallObject(func, args);
			Py_XDECREF(func);
			Py_XDECREF(args);
			if (retval)
			{
				threadlog() << "returned: " << py_repr(retval);
				Py_XDECREF(retval);
			}
			else
			{
				PyObject *type_o, *value_o, *traceback_o;
				PyErr_Fetch(&type_o, &value_o, &traceback_o);
				std::string errvalue = py_repr(value_o);
				privmsg(d_channel) << "ACTION kijkt gestoord op en roept: " << errvalue << ", en gaat daarna weer verder";
				threadlog() << "PY: ERROR: " << errvalue << " " << (type_o ? py_repr(type_o) : "");
				if (value_o)
				{
					Py_XDECREF(value_o);
				}
				if (type_o)
				{
					Py_XDECREF(type_o);
				}
				if (traceback_o)
				{
					print_traceback(traceback_o);
					Py_XDECREF(traceback_o);
				}
			}
		}
		catch(const std::exception &e)
		{
			threadlog() << "exception in thread: " << e.what();
			privmsg(d_channel) << "ACTION schoffelt een '" << e.what() << "'-melding onder het tapijt";
		}
	}
	threadlog() << "thread ended";
	delete this; // note: delete myself
}

#define PY_ASSERT(cond, msg) \
	if (!(cond)) { PyErr_SetString(PyExc_RuntimeError, msg); return NULL; }

static PyObject * piet_send(PyObject *self, PyObject *args)
{
	char *cp_channel, *cp_msg;
	int channel_len, msg_len;

	if (!PyArg_Parse(args, "(s#s#)", &cp_channel, &channel_len, &cp_msg, &msg_len))
		return NULL;

	std::string channel(cp_channel, channel_len), msg(cp_msg, msg_len);

	while(!msg.empty())
	{
		std::string::size_type eolpos = msg.find('\n');
		std::string line;
		if (eolpos == std::string::npos) swap(line,msg); else { line = msg.substr(0, eolpos); msg.erase(0, eolpos+1); }

		if (strncmp(line.c_str(), "ACTION ", 7)==0)
			privmsg(channel) << '\001' << line << '\001';
		else if (strncmp(line.c_str(), "NICK ", 5)==0)
		{
			privmsg(channel) << "wuh? nieuwe nick? wat is dit voor nonsens";
			send("NICK :%s\n", line.c_str()+5);
		}
		else if (strncmp(line.c_str(), "TOPIC ", 6)==0)
			send("TOPIC %s :%s\n", channel.c_str(), line.c_str()+6);
		else
			privmsg(channel) << line;
	}
	
	Py_INCREF( Py_None );
	return Py_None;
}

static PyObject * piet_names(PyObject *self, PyObject *args)
{
	char *cp_channel;
	if (!PyArg_Parse(args, "(s)", &cp_channel))
		return NULL;

	send("NAMES %s\n", cp_channel);

	Py_INCREF( Py_None );
	return Py_None;
}

// will return the old nick if called without parameters
static PyObject * piet_nick(PyObject *self, PyObject *args)
{
	PY_ASSERT(PyTuple_Check(args), "need tuple argument");
	int n = PyTuple_Size(args);
	PY_ASSERT(n==0 || n==1, "need either no arguments or one");

	if (n==0)
		return PyUnicode_FromString(g_config.get_nick().c_str());

	std::string nick = pyunicode_asstring(PyTuple_GetItem(args, 0));
	g_config.set_nick(nick);

	Py_INCREF( Py_None );
	return Py_None;
}

static PyObject * piet_thread(PyObject *self, PyObject *args_)
{
	threadlog() << "piet_thread(" << py_repr(args_) << ")";

	// call like:
	// piet.thread(channel, command, args)
	// command will be called like command(channel, args)

	char *cp_channel, *cp_cmd, *cp_args;
	int channel_len, cmd_len, args_len;

	if (!PyArg_Parse(args_, "(s#s#s#)", 
				&cp_channel, &channel_len, 
				&cp_cmd, &cmd_len, 
				&cp_args, &args_len))
		return NULL;

	std::string channel(cp_channel, channel_len);
	std::string cmd(cp_cmd, cmd_len);
	std::string args(cp_args, args_len);
	threadlocalmap_t &map = getthreadlocalmap();

	PY_ASSERT(map.find("nick") != map.end(), "cannot find nick in threadlocal-environment");
	PY_ASSERT(map.find("auth") != map.end(), "cannot find auth in threadlocal-environment");
	std::string nick = map["nick"];
	uint32_t auth = boost::lexical_cast<uint32_t>(map["auth"]);

	py_handler_t::instance().exec(channel, nick, auth, cmd, args);

	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject * piet_log(PyObject *self, PyObject *args)
{
	char *cp_text;
	int text_len;

	if (!PyArg_Parse(args, "(s#)", &cp_text, &text_len))
		return NULL;

	std::string text(cp_text, text_len);

	threadlog() << text;
	
	Py_INCREF( Py_None );
	return Py_None;
}

static PyObject * piet_op(PyObject *self, PyObject *args)
{
	PY_ASSERT(PyTuple_Check(args), "need tuple argument");

	PY_ASSERT(PyTuple_Size(args), "need 2 arguments, a channel and a list of names");
	PY_ASSERT(PyUnicode_Check(PyTuple_GetItem(args, 0)), "1st argument should be a string");
	PY_ASSERT(PyList_Check(PyTuple_GetItem(args, 1)), "2nd argument should be list of names");
	std::string channel=pyunicode_asstring(PyTuple_GetItem(args, 0));
	PyObject *oblist = PyTuple_GetItem(args, 1);
	
	std::string nm;
	int n=0;
	for (int m=0; m<PyList_Size(oblist); ++m)
	{
		nm +=" "+pyunicode_asstring(PyList_GetItem(oblist, m));
		++n;
		if (n>=3)
		{ // full, send away
			send("MODE %s +%s%s\n", channel.c_str(),
					std::string(n, 'o').c_str(), nm.c_str());
			nm.clear(); n=0;
		}

	}
	if (n)
		send("MODE %s +%s%s\n", channel.c_str(),
				std::string(n, 'o').c_str(), nm.c_str());

	Py_INCREF(Py_None);
	return Py_None;
}

static PyMethodDef piet_methods[] =
{
	{"send", piet_send, METH_VARARGS, NULL},
	{"names", piet_names, METH_VARARGS, NULL},
	{"db", piet_db_query, METH_VARARGS, NULL},
	{"nick", piet_nick, METH_VARARGS, NULL},
	{"thread", piet_thread, METH_VARARGS, NULL},
	{"log", piet_log, METH_VARARGS, NULL},
	{"op", piet_op, METH_VARARGS, NULL},
	{NULL, NULL, 0, NULL}
};

static struct PyModuleDef moduledef = {
	PyModuleDef_HEAD_INIT,
	"piet",              /* m_name */
	NULL,                /* m_doc */
	-1,                  /* m_size */
	piet_methods,        /* m_methods */
	NULL,                /* m_reload */
	NULL,                /* m_traverse */
	NULL,                /* m_clear */
	NULL,                /* m_free */
};

static PyObject *PyInit_piet()
{
	return PyModule_Create(&moduledef);
}

void py_handler_t::export_piet_funcs()
{
	int r = PyImport_AppendInittab("piet", &PyInit_piet);
	if (r != 0)
		throw std::runtime_error("Could not export piet library");
}

