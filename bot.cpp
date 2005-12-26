

#include "bot.h"
#include <fstream>
#include <iostream>
#include <boost/algorithm/string/trim.hpp>
#include <boost/algorithm/string/predicate.hpp>

std::string trimquotes(const std::string &inp_)
{
	if (inp_.size()<2)
		return inp_;
	if (inp_[0]=='"' && inp_[inp_.size()-1]=='"')
		return inp_.substr(1, inp_.size()-2);
	return inp_;
}

c_piet_config::c_piet_config() :
	_server("irc.xs4all.nl"), _service("ircd"),
	_initial_nick("rarepiet"), _channel("#piettest")
{
	try
	{
		std::ifstream i("piet.conf");
		char line[1024];
		while (i.getline(line, 1024))
		{
			char *p=strchr(line, '=');
			if (p && p[0]!='#' && p[0]!='-')
			{
				std::string key(line, p);
				std::string value(p+1);
				boost::algorithm::trim(key);
				boost::algorithm::trim(value);
				key=trimquotes(key);
				value=trimquotes(value);
				if (boost::algorithm::iequals(key, "server"))
					_server=value;
				else if (boost::algorithm::iequals(key, "service"))
					_service=value;
				else if (boost::algorithm::iequals(key, "initial_nick"))
					_initial_nick=value;
				else if (boost::algorithm::iequals(key, "channel"))
					_channel=value;
			}
		}

		_nick=_initial_nick;
	}
	catch (std::exception &e)
	{
		std::cout << "exception reading configuration: " << e.what() << "\n";
	}
}

c_piet_config g_config;


