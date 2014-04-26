#ifndef __PIET_SSLSOCKET_H__
#define __PIET_SSLSOCKET_H__

#include <boost/function.hpp>
#include <boost/asio.hpp>
#include <boost/asio/ssl.hpp>

typedef boost::function<void(const boost::system::error_code &, std::size_t)> asio_callback_t;

struct base_socket_t
{
	virtual void async_read_until_newline(
			boost::asio::streambuf &streambuf,
			asio_callback_t &&cb) = 0;

	virtual void async_write(
			boost::asio::const_buffers_1 &streambuf,
			asio_callback_t &&cb) = 0;
};


class plainsocket_t : public base_socket_t
{
public:
	plainsocket_t(
			boost::asio::io_service &io_service,
			const std::string &host,
			const std::string &service
			);
	virtual ~plainsocket_t();

	void async_read_until_newline(
			boost::asio::streambuf &streambuf,
			asio_callback_t &&cb);

	virtual void async_write(
			boost::asio::const_buffers_1 &streambuf,
			asio_callback_t &&cb);

protected:
	boost::asio::ip::tcp::socket d_socket;
};


class sslsocket_t : public base_socket_t
{
public:
	sslsocket_t(
			boost::asio::io_service &io_service,
			const std::string &host,
			const std::string &service,
			const std::string &servercert = std::string()
			);
	virtual ~sslsocket_t();

	void async_read_until_newline(
			boost::asio::streambuf &streambuf,
			asio_callback_t &&cb);

	virtual void async_write(
			boost::asio::const_buffers_1 &streambuf,
			asio_callback_t &&cb);

protected:
	boost::asio::ssl::context d_ssl_ctx;
	boost::asio::ssl::stream<boost::asio::ip::tcp::socket> d_ssl_socket;
};

#endif // __PIET_SSLSOCKET_H__
