
#include <Python.h>
#include <iostream>
#include <boost/format.hpp>
#include "piet_db.h"
#include "piet_py_handler.h"
#include "privmsg_and_log.h"
#include "sqlite3.h"

namespace
{
struct sqlite_t
{
	public:
	~sqlite_t()
	{
		int r=pthread_key_delete(_key);
		if (r) threadlog() << "DB: failed to destroy key, errorcode " << r << "\n";
	}

	static sqlite_t &instance() { static sqlite_t db; return db; }

	operator sqlite3 *() { return get_db(); }

	// try to open
	bool open() { return get_db()!=NULL; }

	private:
	static void dbdestructor(void *dbvoid_)
	{
		sqlite3 *db=static_cast<sqlite3 *>(dbvoid_);
		threadlog() << "DB: closing database for thread\n";
		sqlite3_close(db);
	}
	sqlite_t()
	{
		int r=pthread_key_create(&_key, &dbdestructor);
		if (r) threadlog() << "DB: failed to create key, errorcode " << r << "\n";
	}

	sqlite3 *get_db()
	{
		sqlite3 *db=static_cast<sqlite3 *>(pthread_getspecific(_key));
		if (!db)
		{
			threadlog() << "DB: opening database in thread\n";
			int rc = sqlite3_open("piet.db", &db);
			if (rc)
			{
				threadlog() << "DB: Can't open database: " << sqlite3_errmsg(db) << "\n";
				sqlite3_close(db);
				db=NULL;
			}
			else
			{
				int r=pthread_setspecific(_key, db);
				if (r)
				{
					threadlog() << "DB: failed to set specific, errorcode " << r << "\n";
					sqlite3_close(db);
					db=NULL;
				}
			}
		}
		return db;
	}

	pthread_key_t _key;
};

}


#define PY_ASSERT(cond, msg) \
	if (!(cond)) { PyErr_SetString(PyExc_RuntimeError, msg); return NULL; }

PyObject * piet_db_query(PyObject *self, PyObject *args)
{
	char *cp_query;
	int query_len;

	if (!PyArg_Parse(args, "(s#)", &cp_query, &query_len))
		return NULL;

	std::string query(cp_query, query_len);

	PY_ASSERT(sqlite_t::instance().open(), "database openen was toch echt te moeilijk, andere keer beter");

	int nrow,ncolumn;
	char *err=NULL;
	char **table=NULL;
	int result=
		sqlite3_get_table(sqlite_t::instance(), query.c_str(), &table, &nrow, &ncolumn, &err);
	if (err)
	{
		threadlog() << "DB: query=" << query << "\n";
		threadlog() << "DB: Error" << err << "\n";
		std::string erro(err);
		sqlite3_free(err);
		if (table) sqlite3_free_table(table);
		PY_ASSERT(false, ("enge databasemeneer zei: "+erro).c_str());
	}
	else if (result!=SQLITE_OK)
	{
		threadlog() << "DB: query=" << query << "\n";
		threadlog() << "DB: Error: unknown\n";
		PY_ASSERT(false, "boehoe, database lezen is mislukt");
	}
	else if (ncolumn==0)
	{
		if (table) sqlite3_free_table(table);
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
	threadlog() << "DB: query: " << query << ", result: " << PyString_AsString(repr) << "\n";
	Py_DECREF(repr);
	if (table) sqlite3_free_table(table);
	return list;
}



std::string piet_db_get(const std::string &query_, const std::string &default_)
{
	if (!sqlite_t::instance().open())
	{
		threadlog() << "DB: database not opened, returning default\n";
		return default_;
	}

	threadlog() << "DB: query=" << query_ << "\n";
	int nrow,ncolumn;
	char *err=NULL;
	char **table=NULL;
	int result=
		sqlite3_get_table(sqlite_t::instance(), query_.c_str(), &table, &nrow, &ncolumn, &err);
	if (err)
	{
		threadlog() << "DB: Error: " << err << "\n";
		sqlite3_free(err);
		if (table) sqlite3_free_table(table);
	}
	else if (result!=SQLITE_OK)
	{
		threadlog() << "DB: Error: unknown\n";
	}
	else if (ncolumn==0)
	{}
	else
	{
		std::string result=table[1];
		sqlite3_free_table(table);
		return result;
	}
	
	return default_;
}

void piet_db_set(const std::string &query_)
{
	if (!sqlite_t::instance().open()) throw;

	threadlog() << "DB: query=" << query_ << "\n";
	int nrow,ncolumn;
	char *err=NULL;
	char **table=NULL;
	int result=
		sqlite3_get_table(sqlite_t::instance(), query_.c_str(), &table, &nrow, &ncolumn, &err);
	if (table) sqlite3_free_table(table);
	if (err)
	{
		threadlog() << "DB: Error" << err << "\n";
		sqlite3_free(err);
	}
	else if (result!=SQLITE_OK)
	{
		threadlog() << "DB: Error: unknown\n";
	}
}

