#ifndef __PIET_PRIVMSG_AND_LOG_H__
#define __PIET_PRIVMSG_AND_LOG_H__

#include <string>
#include <boost/lexical_cast.hpp>

namespace piet_intern 
{

template <typename T>
struct line_based_ostream_lookalike_t
{
	line_based_ostream_lookalike_t() {}
	~line_based_ostream_lookalike_t() { if (!d_msg.empty()) self()->send_one_line(d_msg); }

	inline T *self() { return reinterpret_cast<T *>(this); }

	template<typename Q> T &operator <<(const Q &t_)
	{
		d_msg += boost::lexical_cast<std::string>(t_);
		std::string::size_type t;
		while (t = d_msg.find('\n'), t != std::string::npos)
		{
			if (t>0) self()->send_one_line(d_msg.substr(0,t));
			d_msg = d_msg.substr(t+1);
		}
		return *self();
	}

protected:
	std::string d_msg;
};

} // end piet_intern


struct privmsg_t : public piet_intern::line_based_ostream_lookalike_t<privmsg_t>
{
	privmsg_t(const std::string &channel_) : d_channel(channel_) {}
	~privmsg_t() { }

private:
	void send_one_line(const std::string &s_);
	friend class piet_intern::line_based_ostream_lookalike_t<privmsg_t>;
	std::string d_channel;
};
typedef privmsg_t privmsg;


struct threadlog_t : public piet_intern::line_based_ostream_lookalike_t<threadlog_t>
{
	threadlog_t() {}
	~threadlog_t() { }

private:
	void send_one_line(const std::string &s_);
	friend class piet_intern::line_based_ostream_lookalike_t<threadlog_t>;
};
typedef threadlog_t threadlog;



#endif // __PIET_PRIVMSG_AND_LOG_H__
