

#include <Python.h>
#include <pthread.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <netdb.h>
#include <stdarg.h>
#include <stdio.h>
#include <list>
#include <string>
#include "sender.h"
#include "bot.h"
#include "privmsg_and_log.h"
#include "sslclient.h"

extern boost::shared_ptr<pietsocket_t> g_socket;


// split text into 450-character pieces and add it to the send queue
// header and high_prio are just passed through
static void send_one_line(const std::string header, std::string text, bool high_prio)
{
  while (!text.empty())
  {
		std::string::size_type sendlen=text.length();
    if (sendlen>450)
    {
      sendlen=text.find_last_of(' ', 450);
      if ((sendlen<350)||(sendlen==std::string::npos)) sendlen=450;
    }
		std::string sub = text.substr(0, sendlen);
		threadlog() << "SEND" << (high_prio ? "(PRIO)" : "") << ": " << sub << '\n';
		g_socket->send(header + sub + '\n', high_prio);

		while (sendlen < text.size() && text[sendlen] == ' ')
			++sendlen;
    text.erase(0, sendlen);
  }
}

// send a message with priority high if high_prio is true
// the message should be of the format:
//   msg := <header> <text> [\n <text>]
//   header := [:] <headertext>:   (header text may not contain :)
// from all text fields a list of lines is created with every line less-or-equal than 450 chars
// this list of text fields is then added to the send-queue
void sendstr(const std::string msg, bool high_prio)
{
  //printf("SEND: send(\"%s\", %s)\n", unenter(msg).c_str(), (high_prio?"TRUE":"FALSE"));

  std::string header;
  std::string alltext;
  { // extract header
		std::string::size_type p=msg.find_first_of(':', 1);
    if (p!=std::string::npos)
      header=msg.substr(0,p+1), alltext=msg.substr(p+1);
    else
      header.erase(), alltext=msg;
  }

  while (!alltext.empty())
  {
		std::string::size_type enterpos=alltext.find_first_of('\n');
    if (enterpos==std::string::npos)
      send_one_line(header, alltext, high_prio), alltext.erase();
    else
      send_one_line(header, alltext.substr(0, enterpos), high_prio), alltext.erase(0, enterpos+1);
  }
}

// call send, with normal priority
void send(const char *fmt, ...)
{
	va_list ap;
	int size=1024;

	char *p=new char[size];
	va_start(ap, fmt);
	int n = vsnprintf(p, size, fmt, ap);
	va_end(ap);

	if (n <= -1 || n >= size)
	{
		size = n+1; /* precisely what is needed */
		delete[](p); p=new char[size];
		va_start(ap, fmt);
		n = vsnprintf(p, size, fmt, ap);
		va_end(ap);
	}

	assert(n > -1 && n < size);

	sendstr(std::string(p), false);
	delete[](p);
}

// remove all pending items from send-queue
void sender_flush()
{
	g_socket->flush_send_queue();
}

void quit()
{
	if (g_socket)
		g_socket->stop();
}

