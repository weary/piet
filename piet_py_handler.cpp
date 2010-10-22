
#include "piet_py_handler.h"
#include "sender.h"
#include "privmsg_and_log.h"
#include "bot.h"
#include "piet_db.h"
#include <boost/lexical_cast.hpp>
#include <iostream>
#include <stdexcept>
#include <map>

namespace piet_py_intern
{

// protects threadslist and modification map
static pthread_mutex_t g_mutex;
static pthread_key_t g_threadlocalkey;
typedef std::list<piet_py_intern::py_thread_t *> threadlist_t;
static threadlist_t g_threads;

typedef std::map<std::string, time_t> modification_map_t;
static modification_map_t g_modification_map;

static PyThreadState *g_main_thread_state = NULL;


std::string pystring_asstring(PyObject *obj_)
{
	char *data;
	Py_ssize_t len;
	PyString_AsStringAndSize(obj_, &data, &len);
	return std::string(data, len);
}
std::string py_repr(PyObject *obj_)
{
	if (!obj_) return "NULLrepr";
	PyObject *s = PyObject_Repr(obj_);
	std::string r = pystring_asstring(s);
	Py_XDECREF(s);
	return r;
}
std::string py_str(PyObject *obj_)
{
	if (!obj_) return "NULLstr";
	PyObject *s = PyObject_Str(obj_);
	std::string r = pystring_asstring(s);
	Py_XDECREF(s);
	return r;
}
#define to_str(x) boost::lexical_cast<std::string>(x)
void print_traceback(PyObject *tb_)
{
	assert(PyTraceBack_Check(tb_));

	PyObject *pystdout =
		PyDict_GetItemString(
				PyModule_GetDict(
					PyDict_GetItemString(
						PyImport_GetModuleDict(),
						"sys")),
				"stdout");
	PyTraceBack_Print(tb_, pystdout);
}

struct GIL_lock : public boost::noncopyable
{
	GIL_lock(const std::string &occasion_) : d_occasion(occasion_) { PyEval_AcquireLock(); }
	~GIL_lock() { PyEval_ReleaseLock(); }
	std::string d_occasion;
};

struct intern_lock_t // simple lock-wrapper
{
	intern_lock_t() : d_locked_mutex(&g_mutex)
 	{
		pthread_mutex_lock(d_locked_mutex);
	}
	~intern_lock_t() { unlock(); }

	void unlock() {
		if (d_locked_mutex) {
			pthread_mutex_unlock(d_locked_mutex);
			d_locked_mutex = NULL;
		}
	}
protected:
	pthread_mutex_t *d_locked_mutex;
};


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
	py_thread_t(const std::string &channel_, const std::string &nick_, uint32_t auth_, const std::string &cmd_, const std::string &args_) :
		d_channel(channel_), d_nick(nick_), d_auth(auth_), d_cmd(cmd_), d_args(args_), d_count(g_count++)
	{
		intern_lock_t guard;
		g_threads.push_back(this);

		int result = pthread_create(&d_thread, NULL, &py_thread_t::staticrun, this);
		if (result)
		{
			printf("ERROR: failed to create thread, error code %d\n", result);
			delete this;
		}

		pthread_detach(d_thread);
	}
	~py_thread_t()
	{
		intern_lock_t guard;
		g_threads.remove(this);
	}

	static void *staticrun(void *self)
	{
		return reinterpret_cast<py_thread_t *>(self)->run();
	}
	void *run();

	void kill() { pthread_kill(d_thread, SIGTERM); }

	std::string str() const { return "[" + to_str(d_count) + ": " + d_cmd + "(" + d_args + ")]"; }

protected:
	pthread_t d_thread;
	std::string d_channel;
	std::string d_nick;
	uint32_t d_auth;
	std::string d_cmd;
	std::string d_args;
	uint32_t d_count;
	static uint32_t g_count;
};
uint32_t py_thread_t::g_count = 0;

struct terminate_thread_exception_t : public std::exception
{
	const char *what() const throw() { return "terminate"; }
};



} // end namespace piet_py_intern
using namespace piet_py_intern;

static void delete_thread_local(void *p)
{
	delete static_cast<threadlocalmap_t *>(p);
}

// make sure the threading is initialised early
py_handler_t &g_python = py_handler_t::instance();

py_handler_t::py_handler_t() : destructed(false)
{
	pthread_mutex_init(&g_mutex, NULL);
	pthread_key_create(&g_threadlocalkey, &delete_thread_local);

	getthreadlocalmap()["tid"] = "main";
	getthreadlocalmap()["nick"] = "system";
	getthreadlocalmap()["auth"] = "0";

	Py_Initialize();
	PyEval_InitThreads();

	g_main_thread_state = PyThreadState_Get();

	PyEval_ReleaseLock();

	export_piet_funcs();
}

void sigtermhandler(int sig) // will be called in thread-context
{
	throw terminate_thread_exception_t();
}

void py_handler_t::destruct()
{
	if (destructed) return;
	destructed = true;
	threadlog() << "python handler destructed, cleaning up threads";
	{
		sighandler_t oldhandler = signal(SIGTERM, sigtermhandler);

		{
			intern_lock_t guard;
			for(threadlist_t::iterator i = g_threads.begin(); i != g_threads.end(); ++i)
				(*i)->kill();
		}

		while (1) // wait until threads actually finished
	 	{
			{
				intern_lock_t guard;
				if (g_threads.empty()) break;
			}
			usleep(100);
		}
		signal(SIGTERM, oldhandler);
	}

	PyEval_AcquireLock();
	PyThreadState_Swap(g_main_thread_state);
	Py_Finalize();

	pthread_mutex_destroy(&g_mutex);
}


py_handler_t &py_handler_t::py_handler_t::instance()
{
	static py_handler_t instance;
	return instance;
}

void py_handler_t::read_file_if_changed(const std::string &channel_, const std::string &filename_)
{
	assert(!destructed);
	struct stat st;
	int r=stat(filename_.c_str(), &st);
	if (r!=0)
	{
		int e = errno;
		privmsg(channel_) << "Ik kan \"" << filename_ << "\" niet bereiken! (" << mystrerror(e) << ")";
	}
	else
	{
		intern_lock_t guard1;
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
				GIL_lock guard2(__func__);
				PyThreadState_Swap(g_main_thread_state);
				PyRun_SimpleFile(f, filename_.c_str());
				PyThreadState_Swap(NULL);
				fclose(f);
			}
		}
	}
}


void py_handler_t::exec(const std::string &channel_, const std::string &nick_, uint32_t auth_, const std::string &cmd_, const std::string &args_)
{
	assert(!destructed);
	new py_thread_t(channel_, nick_, auth_, cmd_, args_);
}

std::list<std::string> py_handler_t::threadlist() const
{
	std::list<std::string> result;
	intern_lock_t guard;
	for (threadlist_t::const_iterator i = g_threads.begin(); i!=g_threads.end(); ++i)
		result.push_back((*i)->str());
	return result;
};

threadlocalmap_t &getthreadlocalmap()
{
	void *p = pthread_getspecific(g_threadlocalkey);
	if (!p)
	{
		p = new threadlocalmap_t;
		pthread_setspecific(g_threadlocalkey, p);
	}
#if 0
	{
		std::cout << "threadmap: ";
		threadlocalmap_t &tm = *static_cast<threadlocalmap_t *>(p);
		for (threadlocalmap_t::const_iterator i=tm.begin(); i!=tm.end(); ++i)
		{
			std::cout << "(" << i->first << "," << i->second << ") ";
		}
		std::cout << "\n" << std::flush;
	}
#endif
	return *static_cast<threadlocalmap_t *>(p);
}

void *py_thread_t::run()
{
	threadlocalmap_t &locmap = getthreadlocalmap();
	locmap["tid"] = to_str(d_count);
	threadlog() << "thread started\n";
	{
		GIL_lock guard(boost::lexical_cast<std::string>(d_count)+":");

		PyThreadState *threadstate = PyThreadState_New(g_main_thread_state->interp);
		assert(threadstate);
		PyThreadState_Swap(threadstate);
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
			PyTuple_SetItem(args, 0, PyString_FromStringAndSize(d_channel.data(), d_channel.size()));
			PyTuple_SetItem(args, 1, PyString_FromStringAndSize(d_nick.data(), d_nick.size()));
			PyTuple_SetItem(args, 2, PyInt_FromLong(d_auth));
			PyTuple_SetItem(args, 3, PyString_FromStringAndSize(d_args.data(), d_args.size()));
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
				if (value_o) { Py_XDECREF(value_o); }
				if (type_o) { Py_XDECREF(type_o); }
				if (traceback_o) { print_traceback(traceback_o); Py_XDECREF(traceback_o); }
			}
		}
		catch(const std::exception &e)
		{
			threadlog() << "exception in thread: " << e.what();
			privmsg(d_channel) << "ACTION schoffelt een '" << e.what() << "'-melding onder het tapijt";
		}
		PyThreadState_Swap(NULL);
		PyThreadState_Clear(threadstate);
		PyThreadState_Delete(threadstate);
	}
	threadlog() << "thread ended";
	delete this; // note: delete myself
	return NULL;
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
			send(":%s NICK :%s\n", g_config.get_nick().c_str(), line.c_str()+5);
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

	send(":%s NAMES %s\n", g_config.get_nick().c_str(), cp_channel);

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
		return PyString_FromString(g_config.get_nick().c_str());

	std::string nick = pystring_asstring(PyTuple_GetItem(args, 0));
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

	threadlocalmap_t::const_iterator i = map.find("nick");
	PY_ASSERT(map.find("nick") != map.end(), "cannot find nick in pthread-environment");
	PY_ASSERT(map.find("auth") != map.end(), "cannot find auth in pthread-environment");
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
	PY_ASSERT(PyString_Check(PyTuple_GetItem(args, 0)), "1st argument should be a string");
	PY_ASSERT(PyList_Check(PyTuple_GetItem(args, 1)), "2nd argument should be list of names");
	std::string channel=pystring_asstring(PyTuple_GetItem(args, 0));
	PyObject *oblist = PyTuple_GetItem(args, 1);
	
	std::string nm;
	int n=0;
	for (int m=0; m<PyList_Size(oblist); ++m)
	{
		nm+=std::string(" ")+pystring_asstring(PyList_GetItem(oblist, m));
		++n;
		if (n>=3)
		{ // full, send away
			send(":%s MODE %s +%s%s\n", g_config.get_nick().c_str(), channel.c_str(),
					std::string(n, 'o').c_str(), nm.c_str());
			nm.clear(); n=0;
		}

	}
	if (n)
		send(":%s MODE %s +%s%s\n", g_config.get_nick().c_str(), channel.c_str(),
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





void py_handler_t::export_piet_funcs()
{
	GIL_lock guard(__func__);

	PyImport_AddModule("piet");
	Py_InitModule("piet", piet_methods);
}

