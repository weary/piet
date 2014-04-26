#include "bot.h"
#include <fstream>
#include <iostream>
#include <boost/algorithm/string/trim.hpp>
#include <boost/algorithm/string/predicate.hpp>

static std::string trimquotes(const std::string &inp_)
{
	if (inp_.size()<2)
		return inp_;
	if (inp_[0]=='"' && inp_[inp_.size()-1]=='"')
		return inp_.substr(1, inp_.size()-2);
	return inp_;
}

static bool parse_bool(const std::string &value)
{
	if (boost::algorithm::iequals(value, "true") || value == "0")
		return true;
	if (boost::algorithm::iequals(value, "false") || value == "1")
		return false;
	throw std::runtime_error("invalid boolean value '" + value + "'");
}

c_piet_config::c_piet_config() :
	_server("no-server-configured"), _port(6667),
	_initial_nick("piet"), _channel("#piettest")
{
	try
	{
		std::ifstream i("piet.conf");
		char line[1024];
		bool have_ssl_config;
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
				else if (boost::algorithm::iequals(key, "port"))
				{
					int port=atoi(value.c_str());
					if (port>0)
						_port=port;
					else
						std::cout << "invalid port: " << value << "\n";
				}
				else if (boost::algorithm::iequals(key, "initial_nick"))
					_initial_nick=value;
				else if (boost::algorithm::iequals(key, "channel"))
					_channel=value;
				else if (boost::algorithm::iequals(key, "channelkey"))
					_channel_key=value;
				else if (boost::algorithm::iequals(key, "use_ssl"))
				{
					have_ssl_config=true;
					_use_ssl=parse_bool(value);
				}
				else if (boost::algorithm::iequals(key, "ssl_server_cert"))
					_ssl_server_cert = value;
			}
		}

		if (!have_ssl_config)
			_use_ssl = _port==6697;

		_nick=_initial_nick;
		assert(!_nick.empty() || !"need an initail nick");
	}
	catch (std::exception &e)
	{
		std::cout << "exception reading configuration: " << e.what() << "\n";
	}
}

c_piet_config g_config;


