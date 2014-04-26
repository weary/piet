#ifndef __PIET_BOT_H__
#define __PIET_BOT_H__

#include <string>
#include <vector>
#include <boost/lexical_cast.hpp>

class c_piet_config // global variable g_config can be used to access this one
{
	public:
		c_piet_config();
		~c_piet_config() {}

		// initial configuration
		const std::string &get_server() const { return _server; }
		const int &get_port() const { return _port; }

		const std::string &get_initial_nick() const { return _initial_nick; }
		const std::string &get_channel() const { return _channel; }
		const std::string &get_channel_key() const { return _channel_key; }

		bool use_ssl() const { return _use_ssl; }
		const std::string &ssl_server_certificate() const { return _ssl_server_cert; }

		// changing configuration
		const std::string &get_nick() const { return _nick; }
		void set_nick(const std::string &nick) { _nick=nick; }

	protected:
		std::string _server;
		int _port;
		std::string _initial_nick;
		std::string _channel;
		std::string _channel_key;

		bool _use_ssl;
		std::string _ssl_server_cert;

		std::string _nick;
};
extern c_piet_config g_config;
extern bool g_restart;

int Authenticate(const std::string &nick, const std::string &email);
void Feedback(const std::string &nick, int auth, const std::string &channel, const std::string &msg);

template<typename T>
std::string to_str(const T&t_) { return boost::lexical_cast<std::string,T>(t_); }

#endif // __PIET_BOT_H__
