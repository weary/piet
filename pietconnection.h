#ifndef __PIET_PIETSOCKET_H__
#define __PIET_PIETSOCKET_H__

#include <boost/asio.hpp>
#include <boost/asio/ssl.hpp>
#include <list>

using boost::asio::ip::tcp;
namespace ssl = boost::asio::ssl;

// all lines read are passed to this function
extern void interpret(const std::string &line);

class pietconnection_t
{
public:
	pietconnection_t(
			const std::string &host,
			const std::string &service,
			const std::string &servercert = std::string());

	~pietconnection_t();

	void run();

	void stop();

	// line must include \n
	void send(const std::string &line, bool prio=false);
	void flush_send_queue() { d_send_list.clear(); }

protected:

	void start_read();

	void handle_read(const boost::system::error_code& ec);

	void write_wait(const boost::system::error_code& e);
	void write_loop(const boost::system::error_code& e);

	bool d_stopped;
	boost::asio::io_service d_io_service;
	ssl::context d_ssl_ctx;
	ssl::stream<tcp::socket> d_ssl_socket;

	boost::asio::streambuf d_input_buffer;

	// send + throtling
	std::list<std::string> d_send_list;
	unsigned d_send_counter;
	unsigned d_ping_timer;

	boost::asio::deadline_timer d_sectimer;
};


#endif // __PIET_PIETSOCKET_H__
