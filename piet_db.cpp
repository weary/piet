
#include <Python.h>
#include <iostream>
#include <boost/format.hpp>
#include "piet_db.h"
#include "piet_py_handler.h"
#include "privmsg_and_log.h"
#include "sqlite3.h"

namespace
{

struct sqlite_singleton_t
{
	friend class locked_sqlite;
public:
	~sqlite_singleton_t()
 	{
		if (d_db) close_db();
	}

protected:
	sqlite3 *claim_locked()
	{
		pthread_mutex_lock(&d_mutex);
		//threadlog() << "DB: database claimed";
		if (!d_db) open_db();
		return d_db;
	}

	void release()
	{
		//threadlog() << "DB: database released";
		pthread_mutex_unlock(&d_mutex);
	}

	static sqlite_singleton_t &instance()
	{
		static sqlite_singleton_t g;
		return g;
	}

private:
	sqlite_singleton_t() : d_db(NULL)
	{
		pthread_mutex_init(&d_mutex, NULL);
	}

	void open_db()
	{
		threadlog() << "DB: opening database";
		int rc = sqlite3_open("piet.db", &d_db);
		if (rc)
		{
			threadlog() << "DB: Can't open database: " << sqlite3_errmsg(d_db);
			sqlite3_close(d_db);
			d_db=NULL;
		}
	}

	void close_db()
	{
		threadlog() << "DB: closing database";
		sqlite3_close(d_db);
		d_db = NULL;
	}

	sqlite3 *d_db;
	pthread_mutex_t d_mutex; // only one thread allowed to talk to the database
};

struct locked_sqlite
{
	locked_sqlite() : d_db(sqlite_singleton_t::instance().claim_locked())
	{
	}

	operator sqlite3 *() { return d_db; } // returns NULL if database failed to open

	~locked_sqlite()
	{
		sqlite_singleton_t::instance().release();
	}

protected:
	sqlite3 *d_db;
};

} // nameless namespace

#define PY_ASSERT(cond, msg) \
	if (!(cond)) { PyErr_SetString(PyExc_RuntimeError, msg); return NULL; }

PyObject * piet_db_query(PyObject *self, PyObject *args)
{
	char *cp_query;
	int query_len;

	if (!PyArg_Parse(args, "(s#)", &cp_query, &query_len))
		return NULL;

	std::string query(cp_query, query_len);

	locked_sqlite dbhandle;
	PY_ASSERT((sqlite3 *)dbhandle, "database openen was toch echt te moeilijk, andere keer beter");

	int nrow,ncolumn;
	char *err=NULL;
	char **table=NULL;
	int result=
		sqlite3_get_table(dbhandle, query.c_str(), &table, &nrow, &ncolumn, &err);
	if (err)
	{
		threadlog() << "DB: query: " << query << " -> FAILED";
		threadlog() << "DB: Error " << err;
		std::string erro(err);
		sqlite3_free(err);
		if (table) sqlite3_free_table(table);
		PY_ASSERT(false, ("enge databasemeneer zei: "+erro).c_str());
	}
	else if (result!=SQLITE_OK)
	{
		threadlog() << "DB: query: " << query << " -> FAILED";
		threadlog() << "DB: Error: unknown";
		PY_ASSERT(false, "boehoe, database lezen is mislukt");
	}
	else if (ncolumn==0)
	{
		if (table) sqlite3_free_table(table);
		threadlog() << "DB: query: " << query << " -> no result";
		Py_INCREF(Py_None);
		return Py_None;
	}

	PyObject *list = PyList_New(nrow+1);
	char **field=table;
	for (int n=0; n<=nrow; ++n) // one more row, also heading
	{
		PyObject *subl = PyList_New(ncolumn);
		assert(subl);
		for (int m=0; m<ncolumn; ++m, ++field)
		{
			PyObject *fld = NULL;
			if (*field)
			{
				fld = PyString_FromString(*(field));
			}
			else
			{
				Py_INCREF(Py_None); fld=Py_None;
			}
			assert(fld);
			int r = PyList_SetItem(subl, m, fld);
			assert(r==0);
		}
		int r = PyList_SetItem(list, n, subl);
		assert(r==0);
	}
	PyObject *repr = PyObject_Repr(list);
	threadlog() << "DB: query: " << query << " -> " << PyString_AsString(repr);
	Py_DECREF(repr);
	if (table) sqlite3_free_table(table);
	return list;
}



std::string piet_db_get(const std::string &query_, const std::string &default_)
{
	locked_sqlite dbhandle;
	if (!(sqlite3 *)dbhandle)
	{
		threadlog() << "DB: query: " << query_ << " -> FAILED";
		threadlog() << "DB: database not opened, returning default";
		return default_;
	}

	int nrow,ncolumn;
	char *err=NULL;
	char **table=NULL;
	int result=
		sqlite3_get_table(dbhandle, query_.c_str(), &table, &nrow, &ncolumn, &err);
	if (err)
	{
		threadlog() << "DB: query: " << query_ << " -> FAILED";
		threadlog() << "DB: Error: " << err;
		sqlite3_free(err);
		if (table) sqlite3_free_table(table);
	}
	else if (result!=SQLITE_OK)
	{
		threadlog() << "DB: query: " << query_ << " -> FAILED";
		threadlog() << "DB: Error: unknown";
	}
	else if (ncolumn==0)
	{
		threadlog() << "DB: query: " << query_ << " -> no result";
	}
	else
	{
		std::string result=table[1];
		threadlog() << "DB: query: " << query_ << " -> \"" << result << "\"";
		sqlite3_free_table(table);
		return result;
	}
	
	threadlog() << "DB: returning default: \"" << default_ << "\"";
	return default_;
}

void piet_db_set(const std::string &query_)
{
	threadlog() << "DB: query: " << query_;

	locked_sqlite dbhandle;
	if (!(sqlite3 *)dbhandle)
		throw std::runtime_error("could not open database");

	int nrow,ncolumn;
	char *err=NULL;
	char **table=NULL;
	int result=
		sqlite3_get_table(dbhandle, query_.c_str(), &table, &nrow, &ncolumn, &err);
	if (table) sqlite3_free_table(table);
	if (err)
	{
		threadlog() << "DB: Error" << err;
		sqlite3_free(err);
	}
	else if (result!=SQLITE_OK)
	{
		threadlog() << "DB: Error: unknown";
	}
}

