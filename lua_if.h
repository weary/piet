#ifndef __PIET_CLUA__
#define __PIET_CLUA__


#include <lubi.h>

struct clua
{
	lubi::lua_state _state;
	std::string _current_channel;
	
	clua();
	~clua();

	void server_msg(const std::string &nick, int auth, const std::string &channel, const std::string &msg);
};

extern boost::shared_ptr<clua> lua_inst;

#endif // __PIET_CLUA__
