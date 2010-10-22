
#include <Python.h>
#include "privmsg_and_log.h"
#include "sender.h"
#include "bot.h"
#include "piet_py_handler.h"
#include <assert.h>

namespace piet_intern 
{

} // namespace piet_intern
	
void privmsg_t::send_one_line(const std::string &s_)
{
	assert(!s_.empty() && s_ != "\n" && *s_.rbegin()!='\n');
	std::string pietnick = g_config.get_nick();
	send(":%s PRIVMSG %s :%s\n", pietnick.c_str(),
		 	d_channel.c_str(), s_.c_str());
}

void threadlog_t::send_one_line(const std::string &s_)
{
	assert(!s_.empty() && s_ != "\n" && *s_.rbegin()!='\n');
	threadlocalmap_t &map = getthreadlocalmap();
	threadlocalmap_t::const_iterator i = map.find("tid");
	std::string tid = (i != map.end() ? i->second : "unknown");
	printf("[%s] %s\n", tid.c_str(), s_.c_str());
}

