
#include <string>
#include <ios>
#include <fstream>
#include "bot.h"
#include <boost/bind.hpp>
extern "C" {
#include <lua.h>
#include <lualib.h>
}
#include <luabind/luabind.hpp>
using namespace luabind;

lua_State *L=NULL;

std::string current_channel;

// split(string, splitchar)
int lua_split(lua_State *L)
{
  int paramcount=lua_gettop(L);
  char splitchar=' ';
  const char *source=NULL;
  if (paramcount==1)
    source=lua_tostring(L, 1);
  else if (paramcount==2)
    source=lua_tostring(L, 1),splitchar=lua_tostring(L,2)[0];
  else
  {
    lua_pushstring(L, "invalid parameter count in call to split");
    lua_error(L);
  }

  lua_newtable(L);
  const char *p=source;
  const char *oldp=source;
  int i=1;
  while (oldp=p,p=strchr(oldp,splitchar))
  {
    lua_pushlstring(L, oldp,p-oldp);
    lua_rawseti(L, -2, i);
    p++; i++;
  }
  lua_pushstring(L, oldp);
  lua_rawseti(L, -2, i);
  
  return(1);
}

int lua_sendspecial(lua_State *L)
{
  int n=lua_gettop(L);
  std::string s;
  for (int i=1; i<=n; i++)
  {
    s+=lua_tostring(L, i);
  }
  send(":%s %s", pietnick.c_str(), s.c_str());
  return(0);
}

	
void lua_send(const std::string &str)
{
  //std::string s=":"+pietnick+" PRIVMSG "+current_channel+" :"+str;
  send(":%s PRIVMSG %s :%s", pietnick.c_str(), current_channel.c_str(), str.c_str());
}

int panic(lua_State *l)
{
	printf("LD: paniek!\n");
	printf("LD: lua zei: %s\n", lua_tostring(L, -1));
	return 0;
}

struct clua
{
	clua()
	{
		L=lua_open();
		lua_atpanic(L, &panic);
		luaopen_base(L);
		luaopen_io(L);
		luaopen_math(L);
		luaopen_string(L);
		luaopen_table(L);

		module(L)
		[
			def("send", &lua_send),
			def("sendspecial", &lua_sendspecial),
			def("split", &lua_split)
		];
		//lua_register(L, "send", lua_send);
		//lua_register(L, "sendspecial", lua_sendspecial);
		//lua_register(L, "split", lua_split);

		lua_getglobal(L, "dofile");
		lua_pushstring(L, "server.lua");
		lua_call(L, 1, 0);
		printf("LD: lua_load completed\n");
	}

	~clua()
	{
		lua_close(L);
	}

} lua_inst;

void lua_server_msg(const char *nick, int auth, const char *channel, const char *msg)
{
  std::string m=msg;
  std::string::size_type p=m.find(pietnick);
  if (p!=std::string::npos)
  {
    printf("LUADEBUG: ah, m'n nick gevonden\n");
    m=m.substr(0, p)+"piet"+m.substr(p+pietnick.length(), std::string::npos);
  }

  current_channel=channel;
  lua_getglobal(L, "servermsg");
  //printf("LD: ik ga \"%s\" pushen\n", (pietnick==nick?"piet":nick));
  lua_pushstring(L, (pietnick==nick?"piet":nick));
  //printf("LD: ik ga %d pushen\n", auth);
  lua_pushnumber(L, auth);
  //printf("LD: ik ga \"%s\" pushen\n", channel);
  lua_pushstring(L, channel);
  //printf("LD: ik ga \"%s\" pushen\n", m.c_str());
  lua_pushstring(L, m.c_str());
  int error=lua_pcall(L, 4, 0, 0);
  if (error)
  {
    const char *msg = lua_tostring(L, -1);
    if (msg)
      printf("LD: lua stierf met: \"%s\"\n", msg);
    else
      printf("LD: lua stierf zonder foutmelding\n");
    lua_pop(L, 1);

    std::string s=":"+pietnick+" PRIVMSG "+current_channel+" :lua fout, sorry";
    send("%s", s.c_str());
  }
}

