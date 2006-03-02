#include <boost/noncopyable.hpp>
#include <string>
#include <list>
#include <time.h>
#include <pthread.h>

struct atd_entry
{
	time_t _when;
	std::string _file;
	std::string _channel;
	std::string _command;
	std::string _param;
};
typedef std::list<atd_entry> atd_entry_list_t;

inline bool operator <(const atd_entry &lhs_, const atd_entry &rhs_)
{ return lhs_._when<rhs_._when; }

// named after the at-daemon, sceduler in piet
struct atd_t : boost::noncopyable
{
	~atd_t();

	// return list of entries that are before or at the given time 
	void pop_until(time_t t_, atd_entry_list_t &l_);

	void at(time_t when_,
			const std::string &file_,
			const std::string &channel_,
			const std::string &command_,
			const std::string &param_);

	static atd_t &instance()
	{
		static atd_t atd;
		return atd;
	}
protected:
	atd_entry_list_t _list;

	pthread_mutex_t _atdqueue_mutex;

	atd_t();
};
