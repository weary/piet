
#include "atd.h"
#include <algorithm>


atd_t::atd_t()
{
	pthread_mutex_init(&_atdqueue_mutex, NULL);
}

atd_t::~atd_t()
{
	pthread_mutex_destroy(&_atdqueue_mutex);
}

// return list of entries that are before or at the given time 
void atd_t::pop_until(time_t t_, atd_entry_list_t &l_)
{
	pthread_mutex_lock(&_atdqueue_mutex);
	atd_entry e;
	e._when=t_;
	atd_entry_list_t::iterator i=std::upper_bound(_list.begin(), _list.end(), e);
	l_.splice(l_.end(), _list, _list.begin(), i);
	pthread_mutex_unlock(&_atdqueue_mutex);
}

void atd_t::at(time_t when_,
		const std::string &file_,
		const std::string &channel_,
		const std::string &command_,
		const std::string &param_)
{
	atd_entry e;
	e._when=when_;
	e._file=file_;
	e._channel=channel_;
	e._command=command_;
	e._param=param_;

	pthread_mutex_lock(&_atdqueue_mutex);
	_list.push_front(e);
	_list.sort();
	pthread_mutex_unlock(&_atdqueue_mutex);
}

