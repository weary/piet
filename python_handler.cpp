#include "python_handler.h"
#include "bot.h"
#include "sender.h"
#include "piet_db.h"
#include <signal.h>
#include <boost/shared_ptr.hpp>
#include <boost/tokenizer.hpp>
#include <boost/lexical_cast.hpp>
#include <boost/format.hpp>
#include <list>
#include <iostream>

namespace
{

struct pythonthread_data_t
{
	pythonthread_data_t(PyThreadState *threadstate_) : main_thread_state(threadstate_)
	{
		assert(threadstate_);
	}
	~pythonthread_data_t() {}

  pthread_t thread;
  bool ready;
	PyThreadState * main_thread_state;

  // voor de thread
  std::string channel;
  //std::string file;
  python_cmd cmd;
};

std::ostream &operator <<(std::ostream &os_, const pythonthread_data_t &td_)
{
	os_ << "threaddata["
		"chan=" << td_.channel << ", "
		//"file=" << td_.file << ", "
		"cmd=" << td_.cmd << ", ";
	if (td_.ready)
		os_ << "ready";
	else
		os_ << "not ready";
	os_ << "]";
	return os_;
}

}


namespace
{

typedef boost::shared_ptr<pythonthread_data_t> pythonthread_data_ptr;
typedef std::list<pythonthread_data_ptr> pythonthreadlist_t;

static pythonthreadlist_t plist;

void privmsg(const std::string &channel_, const std::string str_)
{
	send(":%s PRIVMSG %s :%s\n", g_config.get_nick().c_str(), channel_.c_str(), str_.c_str());
}

void *python_threadfunc(void *p)
{
	assert(p);
	pythonthread_data_t *data=(pythonthread_data_t *)p;
	std::cout << "PY: threadfunc, data:\n" << *data << "\n";
	std::string chan=data->channel;

	{
		python_lock guard("threadfunc");

		PyInterpreterState * mainInterpreterState = data->main_thread_state->interp;
		PyThreadState * myThreadState = PyThreadState_New(mainInterpreterState);
		PyThreadState_Swap(myThreadState);

		if (!data->cmd._cmd.empty())
		{
			data->cmd();
		}

		PyThreadState_Swap(NULL);
		PyThreadState_Clear(myThreadState);
		PyThreadState_Delete(myThreadState);
	}

	data->ready=true;

	return NULL;
}


static PyObject * piet_send(PyObject *self, PyObject *args)
{
	char *cp_channel, *cp_msg;

	python_lock guard(__PRETTY_FUNCTION__);
	// parse the incoming arguments
	if (!PyArg_Parse(args, "(ss)", &cp_channel, &cp_msg))
	{
		return NULL;
	}
	std::string channel(cp_channel), msg(cp_msg);

  typedef boost::tokenizer<boost::char_separator<char> > tokenizer;
  boost::char_separator<char> sep("\n");
  tokenizer tokens(msg, sep);
  for (tokenizer::iterator it = tokens.begin(); it != tokens.end(); ++it)
	{
		std::cout << "PY: sendline: " << *it << "*\n";
		privmsg(channel, *it);
	}
	
	Py_INCREF( Py_None );
	return Py_None;
}

#define PY_ASSERT(cond, msg) \
	if (!(cond)) { \
		PyErr_SetString(PyExc_RuntimeError, msg); \
		return NULL; }


// will return the old nick if called without parameters
static PyObject * piet_nick(PyObject *self, PyObject *args)
{
	python_lock guard(__PRETTY_FUNCTION__);

	std::cout << "piet_nick: args=" << python_object(args) << "\n";
	PY_ASSERT(PyTuple_Check(args), "need tuple argument");
	PyTupleObject *t=reinterpret_cast<PyTupleObject *>(args);
	int n=t->ob_size;
	PY_ASSERT(n==0 || n==1, "need either no arguments or one");

	if (n==1)
	{ // got new nick, let's set it
		PY_ASSERT(PyString_Check(t->ob_item[0]), "new nick should be a string");
		std::string nick=PyString_AsString(t->ob_item[0]);
		g_config.set_nick(nick);
		Py_INCREF( Py_None );
		return Py_None;
		//send(":%s NICK :%s\n", g_config.get_nick().c_str(), nick.c_str());
	}

	return PyString_FromString(g_config.get_nick().c_str());
}

static PyObject * piet_names(PyObject *self, PyObject *args)
{
	python_lock guard(__PRETTY_FUNCTION__);

	// parse the incoming arguments
	char *cp_channel;
	if (!PyArg_Parse(args, "s", &cp_channel))
		return NULL;

	send(":%s NAMES %s\n", g_config.get_nick().c_str(), cp_channel);

	Py_INCREF( Py_None );
	return Py_None;
}

static PyObject * piet_thread(PyObject *self, PyObject *args)
{
	python_lock guard(__PRETTY_FUNCTION__);
	std::cout << "piet_thread: args=" << python_object(args) << "\n";
	PY_ASSERT(PyTuple_Check(args), "need tuple argument");

	// call like:
	// piet.thread(func, channel, funcparams...)
	// func will be called like func(channel, funcparams...)

	PyTupleObject *t=reinterpret_cast<PyTupleObject *>(args);
	int n=t->ob_size;
	PY_ASSERT(n>=2, "need at least function and channel parameters");
	PY_ASSERT(PyString_Check(t->ob_item[0]), "function name needs to be specified as string");
	PY_ASSERT(PyString_Check(t->ob_item[1]), "channel is not a string");
	
	std::string cmd_str=PyString_AsString(t->ob_item[0]);
	std::string channel_str=PyString_AsString(t->ob_item[1]);
	std::cout << "piet_thread: cmd=\"" << cmd_str << "\", chan=\"" << channel_str << "\"\n";
	
	python_cmd cmd(channel_str, cmd_str, n-1);

	for (int m=1; m<n; ++m)
	{
		PyObject *p=t->ob_item[m];
		Py_INCREF(p);
		cmd.add_param(p);
	}
	std::cout << "piet_thread: cmd=" << cmd << "\n";

	python_handler::instance().read_and_exec(channel_str, "command.py", cmd);
	
	std::cout << "piet_thread: cmd draait, klaar\n";
#if 0

	python_cmd(g_config.get_channel
	// parse the incoming arguments
	if (!PyArg_Parse(args, "(s)", &nick))
	{
		return NULL;
	}

	send(":%s NICK :%s\n", g_config.get_nick().c_str(), nick);

#endif
	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject * piet_op(PyObject *self, PyObject *args)
{
	python_lock guard(__PRETTY_FUNCTION__);
	std::cout << "piet_op: args=" << python_object(args) << "\n";
	PY_ASSERT(PyTuple_Check(args), "need tuple argument");

	PyTupleObject *t=reinterpret_cast<PyTupleObject *>(args);
	int n=t->ob_size;
	PY_ASSERT(n==2, "need 2 arguments, a channel and a list of names");
	PY_ASSERT(PyString_Check(t->ob_item[0]), "1st argument should be a string");
	PY_ASSERT(PyList_Check(t->ob_item[1]), "2nd argument should be list of names");
	std::string channel=PyString_AsString(t->ob_item[0]);
	PyListObject *names=reinterpret_cast<PyListObject *>(t->ob_item[1]);
	
	std::string nm;
	std::string nm2;
	n=0;
	for (int m=0; m<names->ob_size; ++m)
	{
		nm2+="+o";
		nm+=std::string(" ")+PyString_AsString(names->ob_item[m]);
		++n;
		if (n==3)
		{ // full, send away
			send(":%s MODE %s %s %s\n", g_config.get_nick().c_str(), channel.c_str(),
					nm2.c_str(), nm.c_str());
			nm.clear(); nm2.clear(); n=0;
		}
	}
	if (n>0)
	{
		send(":%s MODE %s %s %s\n", g_config.get_nick().c_str(), channel.c_str(),
				nm2.c_str(), nm.c_str());
	}

	Py_INCREF(Py_None);
	return Py_None;
}



static PyMethodDef piet_methods[] =
{
	{"send", piet_send, METH_OLDARGS, NULL},
	{"names", piet_names, METH_OLDARGS, NULL},
	//{"get", piet_db_get, METH_OLDARGS, NULL},
	//{"set", piet_db_set, METH_OLDARGS, NULL},
	{"db", piet_db_query, METH_OLDARGS, NULL},
	{"nick", piet_nick, METH_VARARGS, NULL},
	{"thread", piet_thread, METH_VARARGS, NULL},
	{"op", piet_op, METH_VARARGS, NULL},
	{NULL, NULL, METH_OLDARGS, NULL}
};

}

python_handler::python_handler() :
	_main_thread_state(NULL)
{
	Py_Initialize();
	PyEval_InitThreads();

	python_lock::global_init();

	_main_thread_state = PyThreadState_Get();

	PyImport_AddModule("piet");
	Py_InitModule("piet", piet_methods);

	PyEval_ReleaseLock();
}

python_handler::~python_handler()
{
	PyEval_AcquireLock();
	Py_Finalize();
	python_lock::global_deinit();
}

std::string mystrerror(int errnum)
{
	char buf[1024];
	assert(strerror_r(errnum, buf, 1024)==0);
	return buf;
}

void python_handler::checkfile_and_read(const std::string channel_, const std::string &file_)
{
	struct stat st;
	int r=stat(file_.c_str(), &st);
	if (r!=0)
	{
		privmsg(channel_, (boost::format("Ik kan \"%1%\" niet bereiken! (%2%)\n") %
					file_ % mystrerror(errno)).str());
	}
	else
	{
		modification_map_t::iterator i=_modification_map.find(file_);
		bool readit=false;
		if (i==_modification_map.end())
		{ // new file, just read, no message
			readit=true;
		}
		else if (i->second!=st.st_mtime)
		{
			privmsg(channel_, "ho! eerst de geweldige nieuwe "+file_+" lezen\n");
			readit=true;
		}

		if (readit)
		{
			python_lock("checkfile_and_read");
			_modification_map[file_]=st.st_mtime;

			std::cout << "PY: reading file \"" << file_ << "\"\n" << std::flush;
			FILE *f=fopen(file_.c_str(), "r");
			if (!f)
				privmsg(channel_, "Failed to open \""+file_+"\"\n");
			else
			{
				PyThreadState_Swap(_main_thread_state);
				PyRun_SimpleFile(f, file_.c_str());
				PyThreadState_Swap(NULL);
				fclose(f);
			}
		}
	}
}

void python_handler::read_and_exec(
		const std::string &channel_,
		const std::string &file_,
		const python_cmd &cmd_)
{
	std::cout << "read_and_exec(\"" << channel_ << "\", \"" << file_ << "\", " << cmd_ << ")\n" << std::flush;
	pythonthread_data_ptr p(new pythonthread_data_t(_main_thread_state));
  p->channel=channel_;
  p->cmd=cmd_;
  p->ready=false;

	checkfile_and_read(channel_, file_);

  int result=pthread_create(&(p->thread), NULL, python_threadfunc, p.get());
  if (result)
  {
    printf("ERROR: failed to create thread, error code %d\n", result);
    return;
  }
  plist.push_back(p);
}

#if 0
void python_handler::read(const std::string &channel_, const std::string &file_)
{
	read_and_exec(channel_, file_, python_cmd());
}

void python_handler::exec(const std::string &channel_, const python_cmd &code_)
{
	read_and_exec(channel_, std::string(), code_);
}
#endif

void python_handler::cleanup()
{
	// clean up the corpses
	
	if (plist.empty())
	{
		std::cout << "GC: nothing to do\n";
		return;
	}
	std::cout << "GC: sequence started\n";
  
  pythonthreadlist_t::iterator i=plist.begin();
  while (i!=plist.end())
  {
		std::cout << "GC: checking " << (*i)->cmd << "\n";
    if((*i)->ready)
    {
			std::cout << "GC: - removing " << (*i)->cmd << "\n";
      pthread_join((*i)->thread, NULL);
      i=plist.erase(i);
    }
    else
      ++i;
  }
	std::cout << "GC: finished\n";
}

void python_handler::killall()
{
  // arg! shutdown! quick! killing spree!
  pythonthreadlist_t::const_iterator i=plist.begin();
  for (i=plist.begin(); i!=plist.end(); ++i)
  {
		std::cout << "GC: killing " << (*i)->cmd << "\n" << std::flush;
    pthread_kill((*i)->thread, SIGKILL);
	}
	
  for (i=plist.begin(); i!=plist.end(); ++i)
	{
		std::cout << "GC: joining " << (*i)->cmd << "\n" << std::flush;
    pthread_join((*i)->thread, NULL);
		std::cout << "GC: finished " << (*i)->cmd << "\n";
	}

  plist.clear();
}

std::list<std::string> python_handler::threadlist()
{
	std::list<std::string> result;

  pythonthreadlist_t::const_iterator i=plist.begin();
  for (i=plist.begin(); i!=plist.end(); ++i)
	{
		result.push_back(
				(boost::format("%1% voor %2%%3%") %
				 boost::lexical_cast<std::string>((*i)->cmd) %
				 (*i)->channel %
				 //(*i)->file %
				 ((*i)->ready?" (eigenlijk al klaar)":"")
				).str());
	}

	return result;
}

