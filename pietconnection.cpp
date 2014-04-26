#include "pietconnection.h"
#include "privmsg_and_log.h"
#include <boost/bind.hpp>

pietconnection_t::pietconnection_t(
		const std::string &host,
		const std::string &service,
		const std::string &servercert) :
	d_stopped(false),
	d_ssl_ctx(ssl::context::sslv23),
	d_ssl_socket(d_io_service, d_ssl_ctx),
	d_send_counter(8),
	d_ping_timer(60),
	d_sectimer(d_io_service, boost::posix_time::seconds(1))
{
	if (!servercert.empty())
	{
		d_ssl_ctx.load_verify_file(servercert.c_str());
		d_ssl_socket.set_verify_mode(ssl::verify_peer);
	}
	else
		d_ssl_socket.set_verify_mode(ssl::verify_none);

	tcp::resolver resolver(d_io_service);
	tcp::resolver::query query(host, service);
	boost::asio::connect(d_ssl_socket.lowest_layer(), resolver.resolve(query));
	d_ssl_socket.lowest_layer().set_option(tcp::no_delay(true));

	d_ssl_socket.set_verify_callback(ssl::rfc2818_verification(host));
	d_ssl_socket.handshake(ssl::stream<tcp::socket>::client);
}

pietconnection_t::~pietconnection_t()
{
	if (!d_stopped)
		d_ssl_socket.shutdown();
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
	boost::asio::async_read_until(d_ssl_socket, d_input_buffer, '\n',
			boost::bind(&pietconnection_t::handle_read, this, _1));
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

	std::string data;
	if (d_send_list.empty())
	{
		if (d_stopped)
		{
			d_ssl_socket.shutdown();
			return;
		}

		--d_ping_timer;
		if (d_ping_timer == 0)
		{
			d_ping_timer = 60;
			data = "PING aap\n";
		}
	}
	else
	{
		d_ping_timer = 60;
		//unsigned oldsize = d_send_list.size();
		while (!d_send_list.empty() && d_send_counter >= 2)
		{
			data += d_send_list.front();
			d_send_list.pop_front();
			d_send_counter  -= 2;
		}
	}

	if (!data.empty())
		boost::asio::async_write(
				d_ssl_socket,
				boost::asio::buffer(data),
				boost::bind(
					&pietconnection_t::write_wait, this,
					boost::asio::placeholders::error));
	else
		write_wait(boost::system::error_code());
}
