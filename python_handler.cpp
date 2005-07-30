#include "python_handler.h"
#include "bot.h"
#include <signal.h>
#include <boost/shared_ptr.hpp>
#include <boost/tokenizer.hpp>
#include <list>
#include <iostream>

namespace
{
struct pythonthread_data_t
{
  pthread_t thread;
  bool ready;
	PyThreadState * main_thread_state;

  // voor de thread
  std::string channel;
  std::string file;
  std::string cmd;
};

typedef boost::shared_ptr<pythonthread_data_t> pythonthread_data_ptr;
struct pythonthreadlist_t : public std::list<pythonthread_data_ptr>
{
};

static pythonthreadlist_t plist;

void privmsg(const std::string &channel_, const std::string str_)
{
	send(":%s PRIVMSG %s :%s\n", g_config.get_nick().c_str(), channel_.c_str(), str_.c_str());
}

void *python_threadfunc(void *p)
{
	assert(p);
	pythonthread_data_t *data=(pythonthread_data_t *)p;
	std::string chan=data->channel;

	PyEval_AcquireLock();
	
	PyInterpreterState * mainInterpreterState = data->main_thread_state->interp;
	PyThreadState * myThreadState = PyThreadState_New(mainInterpreterState);
	PyThreadState_Swap(myThreadState);

	if (!data->file.empty())
	{
		std::cout << "PY: reading file \"" << data->file << "\"\n";
		FILE *f=fopen(data->file.c_str(), "r");
		if (!f)
			privmsg(chan, "Failed to open \""+data->file+"\"\n");
		else
		{
			PyRun_SimpleFile(f, data->file.c_str());
			fclose(f);
		}
	}
	if (!data->cmd.empty())
	{
		std::cout << "PY: executing \"" << data->cmd << "\"\n";
		PyRun_SimpleString(data->cmd.c_str());
	}

	PyThreadState_Swap(NULL);
	PyThreadState_Clear(myThreadState);
	PyThreadState_Delete(myThreadState);
	PyEval_ReleaseLock();

	data->ready=true;

	return NULL;
}


static PyObject * piet_send(PyObject *self, PyObject *args)
{
	char *cp_channel, *cp_msg;
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
		std::cout << "tokenized: -" << *it << "*\n";
		privmsg(channel, *it);
	}
	
	Py_INCREF( Py_None );
	return Py_None;
}

static PyObject * piet_nick(PyObject *self, PyObject *args)
{
	char *nick;
	// parse the incoming arguments
	if (!PyArg_Parse(args, "(s)", &nick))
	{
		return NULL;
	}

	send(":%s NICK :%s\n", g_config.get_nick().c_str(), nick);

	Py_INCREF( Py_None );
	return Py_None;
}

static PyMethodDef piet_methods[] =
{
	{"send", piet_send},
	{"nick", piet_nick},
	{NULL, NULL}
};

}

python_handler::python_handler() :
	_main_thread_state(NULL)
{
	Py_Initialize();
	PyEval_InitThreads();

	_main_thread_state = PyThreadState_Get();

	PyImport_AddModule("piet");
	Py_InitModule("piet", piet_methods);

	PyEval_ReleaseLock();
}

python_handler::~python_handler()
{
	PyEval_AcquireLock();
	Py_Finalize();
}

void python_handler::read_and_exec(
		const std::string &channel_,
		const std::string &file_,
		const std::string &cmd_)
{
	pythonthread_data_ptr p(new pythonthread_data_t);
	p->main_thread_state=_main_thread_state;
  p->channel=channel_;
	p->file=file_;
  p->cmd=cmd_;
  p->ready=false;

  int result=pthread_create(&(p->thread), NULL, python_threadfunc, p.get());
  if (result)
  {
    printf("ERROR: failed to create thread, error code %d\n", result);
    return;
  }
  plist.push_back(p);
}

void python_handler::read(const std::string &channel_, const std::string &file_)
{
	read_and_exec(channel_, file_, std::string());
}

void python_handler::exec(const std::string &channel_, const std::string &code_)
{
	read_and_exec(channel_, std::string(), code_);
}

void python_handler::cleanup()
{
	// clean up the corpses

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
  printf("GC: finished\n");
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
		result.push_back((*i)->cmd);

	return result;
}

