#include "pietconnection.h"
#include "piet_socket.h"
#include "privmsg_and_log.h"
#include <boost/bind.hpp>

pietconnection_t::pietconnection_t() :
	d_stopped(false),
	d_send_counter(8),
	d_ping_timer(60),
	d_sectimer(d_io_service, boost::posix_time::seconds(1))
{}

void pietconnection_t::connect(
		const std::string &host,
		const std::string &service)
{
	d_socket = std::make_shared<plainsocket_t>(
			d_io_service, host, service);
}

void pietconnection_t::connect_ssl(
		const std::string &host,
		const std::string &service,
		const std::string &servercert)
{
	d_socket = std::make_shared<sslsocket_t>(
			d_io_service, host, service, servercert);
}

void pietconnection_t::run()
{
	start_read();
	write_loop(boost::system::error_code());

	d_io_service.run();
}

void pietconnection_t::stop()
{
	d_stopped = true;
}

void pietconnection_t::send(const std::string &line, bool prio)
{
	if (prio)
		d_send_list.push_front(line);
	else
		d_send_list.push_back(line);
}

void pietconnection_t::start_read()
{
	d_socket->async_read_until_newline(d_input_buffer,
			boost::bind(&pietconnection_t::handle_read, this, 
				boost::asio::placeholders::error));
}

void pietconnection_t::handle_read(const boost::system::error_code& ec)
{
	if (ec)
		throw std::runtime_error("Read failed with: " + ec.message());

	std::string line;
	std::istream is(&d_input_buffer);
	std::getline(is, line);

	// strip newlines
	while (!line.empty() && (line[line.size()-1] == '\n' || line[line.size()-1] == '\r'))
		line.erase(line.size()-1);
	threadlog() << "recv: \"" << line << "\"";
	interpret(line);

	start_read();
}

void pietconnection_t::write_wait(const boost::system::error_code& e)
{
	d_sectimer.expires_from_now(boost::posix_time::seconds(1));
	d_sectimer.async_wait(
			boost::bind(
				&pietconnection_t::write_loop,
				this,
				boost::asio::placeholders::error)
			);
}

void pietconnection_t::write_loop(const boost::system::error_code& ec)
{
	if (ec)
		throw std::runtime_error("Write failed with: " + ec.message());

	// we just waited a second
	if (d_send_counter < 8) 
		++d_send_counter;

	d_writebuffer.clear();
	if (d_send_list.empty())
	{
		if (d_stopped)
		{
			d_socket.reset();
			return;
		}

		--d_ping_timer;
		if (d_ping_timer == 0)
		{
			d_ping_timer = 60;
			d_writebuffer = "PING aap\n";
		}
	}
	else
	{
		d_ping_timer = 60;
		//unsigned oldsize = d_send_list.size();
		while (!d_send_list.empty() && d_send_counter >= 2)
		{
			d_writebuffer += d_send_list.front();
			d_send_list.pop_front();
			d_send_counter  -= 2;
		}
	}

	if (!d_writebuffer.empty())
	{
		boost::asio::const_buffers_1 buf = boost::asio::buffer(d_writebuffer);
		d_socket->async_write(
				buf,
				boost::bind(
					&pietconnection_t::write_wait, this,
					boost::asio::placeholders::error));
	}
	else
		write_wait(boost::system::error_code());
}
