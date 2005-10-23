#if 0
#include "bot.h"
#include "sender.h"
#include "lua_if.h"
#include <boost/bind.hpp>
#include <boost/format.hpp>
#include <fstream>
#include <ios>
#include <string>

boost::shared_ptr<clua> lua_inst;

namespace {

std::map<int, std::string> lua_split(const std::string str, char splitchar)
{
  const char *p=str.c_str();
  const char *oldp=p;
  int i=1;
	std::map<int, std::string> result;
  while (oldp=p,p=strchr(oldp,splitchar))
  {
		result.insert(std::pair<int, std::string>(i, std::string(oldp,p)));
    ++p; ++i;
  }
	result.insert(std::pair<int, std::string>(i, std::string(oldp)));
  
  return(result);
}

void lua_sendspecial(std::vector<std::string> txt)
{
  std::string s=std::accumulate(txt.begin(), txt.end(), std::string());
  send(":%s %s", g_config.get_nick().c_str(), s.c_str());
}

	
void lua_send(clua *cl, const std::string str)
{
	assert(cl);
  send(":%s PRIVMSG %s :%s", g_config.get_nick().c_str(), cl->_current_channel.c_str(), str.c_str());
}

}

clua::clua() : _state()
{
	_state.luaopen_io();
	_state.luaopen_math();
	_state.luaopen_string();
	_state.luaopen_table();

	_state["send"]=boost::function<void (std::string)>(
			boost::bind(lua_send, this, _1));
	_state["sendspecial"]=boost::function<void (std::vector<std::string>)>(
			lua_sendspecial);
	_state["split"]=boost::function<std::map<int,std::string>(std::string,
			char)>(lua_split);

	_state.run("dofile(\"server.lua\");");
	printf("LD: lua_load completed\n");
}

clua::~clua()
{
}

void clua::server_msg(const std::string &nick_, int auth_, const std::string &channel_, const std::string &msg_)
{
	std::string msg=msg_;
	std::string pietnick=g_config.get_nick();
  std::string::size_type p=msg.find(pietnick);
  if (p!=std::string::npos)
  {
    //printf("LUADEBUG: ah, m'n nick gevonden\n");
    msg=msg.substr(0, p)+"piet"+msg.substr(p+pietnick.length(), std::string::npos);
  }

	_current_channel=channel_;
	_state["nick"]=nick_;
	_state["auth"]=auth_;
	_state["channel"]=channel_;
	_state["msg"]=msg;
	std::string script=(boost::format("servermsg(\'%1%\', %2%, \'%3%\', \'%4%\')") %
		nick_ % auth_ % channel_ % msg).str();

	printf("LD: going to execute script: %s\n", script.c_str());

	try
	{
		lua_inst->_state.run("servermsg(nick, auth, channel,msg)");
	}
	catch(std::exception &e)
	{
		printf("LD: exception, %s", e.what());
    std::string s=":"+g_config.get_nick()+" PRIVMSG "+_current_channel+" :lua fout, sorry";
    send("%s", s.c_str());
	}
}
#endif
