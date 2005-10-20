
#include "piet_db.h"
#include "python_support.h"
#include "sqlite3.h"
#include <iostream>
#include <boost/format.hpp>

namespace
{
struct sqlite_t
{
	public:
	~sqlite_t()
	{
		int r=pthread_key_delete(_key);
		if (r) std::cout << "DB: failed to destroy key, errorcode " << r << "\n";
	}

	static sqlite_t &instance() { static sqlite_t db; return db; }

	operator sqlite3 *() { return get_db(); }

	// try to open
	bool open() { return get_db()!=NULL; }

	private:
	static void dbdestructor(void *dbvoid_)
	{
		sqlite3 *db=static_cast<sqlite3 *>(dbvoid_);
		std::cout << "DB: closing database for thread " << pthread_self() << "\n";
		sqlite3_close(db);
	}
	sqlite_t()
	{
		int r=pthread_key_create(&_key, &dbdestructor);
		if (r) std::cout << "DB: failed to create key, errorcode " << r << "\n";
	}

	sqlite3 *get_db()
	{
		sqlite3 *db=static_cast<sqlite3 *>(pthread_getspecific(_key));
		if (!db)
		{
			std::cout << "DB: opening database for thread " << pthread_self() << "\n";
			int rc = sqlite3_open("piet.db", &db);
			if (rc)
			{
				std::cout << "DB: Can't open database: " << sqlite3_errmsg(db) << "\n";
				sqlite3_close(db);
				db=NULL;
			}
			else
			{
				int r=pthread_setspecific(_key, db);
				if (r)
				{
					std::cout << "DB: failed to set specific, errorcode " << r << "\n";
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

PyObject * piet_db_query(PyObject *self, PyObject *args)
{
	python_lock guard(__PRETTY_FUNCTION__);
	
	std::string query(PyString_AsString(args));

	if (!sqlite_t::instance().open())
	{
		PyErr_SetString(PyExc_Exception, "database openen was toch echt te moeilijk, andere keer beter");
		return NULL;
	}

	std::cout << "DB: query=" << query << "\n";
	int nrow,ncolumn;
	char *err=NULL;
	char **table=NULL;
	int result=
		sqlite3_get_table(sqlite_t::instance(), query.c_str(), &table, &nrow, &ncolumn, &err);
	if (err)
	{
		std::cout << "DB: Error" << err << "\n";
		PyErr_SetString(PyExc_Exception, (std::string("enge databasemeneer zei: ")+err).c_str());
		sqlite3_free(err);
		if (table) sqlite3_free_table(table);
	}
	else if (result!=SQLITE_OK)
	{
		std::cout << "DB: Error: unknown\n";
		PyErr_SetString(PyExc_Exception, "boehoe, database lezen is mislukt");
	}
	else if (ncolumn==0)
	{
		if (table) sqlite3_free_table(table);
		Py_INCREF(Py_None);
		return Py_None;
	}
	else
	{
		python_object list(PyList_New(nrow+1));
		char **field=table;
		for (int n=0; n<=nrow; ++n) // one more row, also heading
		{
			std::cout << "DB: result: ";
			python_object subl(PyList_New(ncolumn));
			assert(subl);
			for (int m=0; m<ncolumn; ++m, ++field)
			{
				if (m>0) std::cout << " | ";
				python_object fld;
				if (*field)
				{
					std::cout << *field;
					fld = PyString_FromString(*(field));
				}
				else
				{
					std::cout << "NULL";
					Py_INCREF(Py_None); fld=Py_None;
				}
				assert(fld);
				int r=PyList_SetItem(subl, m, fld);
				assert(r==0);
			}
			std::cout << "\n";
			int r=PyList_SetItem(list, n, subl);
			assert(r==0);
		}
		std::cout << std::flush;
		if (table) sqlite3_free_table(table);
		return list;
	}
	
	return NULL;
}

std::string piet_db_get(const std::string &table_, const std::string &key_, const std::string &default_)
{
	if (!sqlite_t::instance().open())
	{
		std::cout << "DB: database not opened, returning default\n";
		return default_;
	}

	std::string query="SELECT value FROM "+table_+" WHERE key='"+key_+"'";
	std::cout << "DB: query=" << query << "\n";
	int nrow,ncolumn;
	char *err=NULL;
	char **table=NULL;
	int result=
		sqlite3_get_table(sqlite_t::instance(), query.c_str(), &table, &nrow, &ncolumn, &err);
	if (err)
	{
		std::cout << "DB: Error: " << err << "\n";
		sqlite3_free(err);
		if (table) sqlite3_free_table(table);
	}
	else if (result!=SQLITE_OK)
	{
		std::cout << "DB: Error: unknown\n";
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

void piet_db_set(const std::string &table_, const std::string &key_, const std::string &value_)
{
	python_lock guard(__PRETTY_FUNCTION__);

	std::string query="REPLACE INTO "+table_+" VALUES('"+key_+"', '"+value_+"')";

	if (!sqlite_t::instance().open()) throw;

	std::cout << "DB: query=" << query << "\n";
	int nrow,ncolumn;
	char *err=NULL;
	char **table=NULL;
	int result=
		sqlite3_get_table(sqlite_t::instance(), query.c_str(), &table, &nrow, &ncolumn, &err);
	if (table) sqlite3_free_table(table);
	if (err)
	{
		std::cout << "DB: Error" << err << "\n";
		sqlite3_free(err);
	}
	else if (result!=SQLITE_OK)
	{
		std::cout << "DB: Error: unknown\n";
	}
}
