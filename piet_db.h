

#ifndef __PIET_DB_H__
#define __PIET_DB_H__

#include <Python.h>
#include <string>
#include <boost/lexical_cast.hpp>

PyObject * piet_db_query(PyObject *self, PyObject *args);

template<typename T>
T piet_db_get(const std::string &table_, const std::string &key_, const T default_)
{
	return boost::lexical_cast<T>(piet_db_get(table_, key_, boost::lexical_cast<std::string>(default_)));
}

template<typename T>
void piet_db_set(const std::string &table_, const std::string &key_, const T value_)
{
	return piet_db_set(table_, key_, boost::lexical_cast<std::string>(value_));
}


std::string piet_db_get(const std::string &table_, const std::string &key_, const std::string &default_);
void piet_db_set(const std::string &table_, const std::string &key_, const std::string &default_);

#endif // __PIET_DB_H__
