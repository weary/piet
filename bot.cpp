

#include "bot.h"
#include <lubi.h>


c_piet_config::c_piet_config() : _server("irc.xs4all.nl"), _service("ircd"),
																 _initial_nick("rarepiet"), _channel("#piettest")
{
	try
	{
		lubi::lua_state state;
		state.run("dofile(\"piet_config.lua\");");
		_server=state["server"].get<std::string>();
		_service=state["service"].get<std::string>();
		_initial_nick=state["initial_nick"].get<std::string>();
		_channel=state["channel"].get<std::string>();

		_nick=_initial_nick;
	}
	catch (std::exception &e)
	{
		std::cout << "exception reading configuration: " << e.what() << "\n";
	}
}

c_piet_config g_config;


