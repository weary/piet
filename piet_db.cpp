
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
		sqlite3_close(_db);
	}

	static sqlite_t &instance() { static sqlite_t db; return db; }

	operator sqlite3 *() { return _db; }
	bool open() { return (_db!=NULL); }

	private:
	sqlite_t()
	{
		int rc = sqlite3_open("piet.db", &_db);
		if (rc)
		{
			std::cout << "DB: Can't open database: " << sqlite3_errmsg(_db) << "\n";
			sqlite3_close(_db);
			_db=NULL;
		}
		else
			std::cout << "DB: database open\n";
	}

	sqlite3 *_db;
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
		return NULL;
	}
	else if (result!=SQLITE_OK)
	{
		PyErr_SetString(PyExc_Exception, "boehoe, database lezen is mislukt");
		return NULL;
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
			python_object subl(PyList_New(ncolumn));
			assert(subl);
			for (int m=0; m<ncolumn; ++m, ++field)
			{
				python_object fld;
				if (*field)
					fld = PyString_FromString(*(field));
				else
				{ Py_INCREF(Py_None); fld=Py_None; }
				assert(fld);
				int r=PyList_SetItem(subl, m, fld);
				assert(r==0);
			}
			int r=PyList_SetItem(list, n, subl);
			assert(r==0);
		}
		if (table) sqlite3_free_table(table);
		return list;
	}
	
	return NULL;
}
