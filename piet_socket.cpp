#include "piet_socket.h"

using boost::asio::ip::tcp;
namespace ssl = boost::asio::ssl;

plainsocket_t::plainsocket_t(
		boost::asio::io_service &io_service,
		const std::string &host,
		const std::string &service) :
	d_socket(io_service)
{
	tcp::resolver resolver(io_service);
	tcp::resolver::query query(host, service);
	boost::asio::connect(d_socket, resolver.resolve(query));
	d_socket.set_option(tcp::no_delay(true));
}

plainsocket_t::~plainsocket_t()
{
	d_socket.close();
}

void plainsocket_t::async_read_until_newline(
		boost::asio::streambuf &streambuf,
		asio_callback_t &&cb)
{
	boost::asio::async_read_until(
			d_socket, streambuf, '\n', std::move(cb));
}

void plainsocket_t::async_write(
		boost::asio::const_buffers_1 &streambuf,
		asio_callback_t &&cb)
{
	boost::asio::async_write(
			d_socket, streambuf, cb);
}

///////////////////////////////////////////////////////////

sslsocket_t::sslsocket_t(
		boost::asio::io_service &io_service,
		const std::string &host,
		const std::string &service,
		const std::string &servercert) :
	d_ssl_ctx(ssl::context::sslv23),
	d_ssl_socket(io_service, d_ssl_ctx)
{
	if (!servercert.empty())
	{
		d_ssl_ctx.load_verify_file(servercert.c_str());
		d_ssl_socket.set_verify_mode(ssl::verify_peer);
	}
	else
		d_ssl_socket.set_verify_mode(ssl::verify_none);

	tcp::resolver resolver(io_service);
	tcp::resolver::query query(host, service);
	boost::asio::connect(d_ssl_socket.lowest_layer(), resolver.resolve(query));
	d_ssl_socket.lowest_layer().set_option(tcp::no_delay(true));

	d_ssl_socket.set_verify_callback(ssl::rfc2818_verification(host));
	d_ssl_socket.handshake(ssl::stream<tcp::socket>::client);
}

sslsocket_t::~sslsocket_t()
{
	d_ssl_socket.shutdown();
}

void sslsocket_t::async_read_until_newline(
		boost::asio::streambuf &streambuf,
		asio_callback_t &&cb)
{
	boost::asio::async_read_until(
			d_ssl_socket, streambuf, '\n', std::move(cb));
}

void sslsocket_t::async_write(
		boost::asio::const_buffers_1 &streambuf,
		asio_callback_t &&cb)
{
	boost::asio::async_write(
			d_ssl_socket, streambuf, cb);
}
