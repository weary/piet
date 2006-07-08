

#ifndef __PIET_DB_H__
#define __PIET_DB_H__

#include <Python.h>
#include <string>
#include <boost/lexical_cast.hpp>

PyObject * piet_db_query(PyObject *self, PyObject *args);

std::string piet_db_get(const std::string &query_, const std::string &default_);

template<typename T>
T piet_db_get(const std::string &query_, const T default_)
{
	return boost::lexical_cast<T>(
			piet_db_get(
				query_,
				boost::lexical_cast<std::string>(default_)));
}

void piet_db_set(const std::string &query_);

#endif // __PIET_DB_H__
