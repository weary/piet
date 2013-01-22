#include "piet_py_handler.h"
#include "bot.h"
#include "sender.h"
#include "piet_db.h"
#include "privmsg_and_log.h"
#include <boost/algorithm/string/replace.hpp>
#include <boost/format.hpp>
#include <crypt.h>
#include <errno.h>
#include <netdb.h>
#include <netinet/in.h>
#include <stdarg.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <sys/poll.h>
#include <iostream>
#include <unistd.h>
#include <signal.h>

using boost::format;

bool quit=false;

void interpret(const std::string &input);

void sighandler(int sig)
{
	quit = true;
}

int connect_to_server(const std::string &addr, int port)
{
	struct hostent *h = gethostbyname(addr.c_str());
	if (!h)
	{
		printf("could not find host \"%s\"\n", addr.c_str());
		throw std::runtime_error("could not find host \"" + addr + "\"");
	}

	printf("connecting to %u.%u.%u.%u:%u\n",
			((unsigned char *)(h->h_addr))[0],
			((unsigned char *)(h->h_addr))[1],
			((unsigned char *)(h->h_addr))[2],
			((unsigned char *)(h->h_addr))[3], port);

	int sok = socket(AF_INET, SOCK_STREAM, 0);
	if (sok == -1)
	{
		printf("failed to create socket\n");
		throw std::runtime_error("failed to create socket");
	}

	struct sockaddr_in sin;
	memset(&sin, 0, sizeof(sin));
	sin.sin_family = AF_INET;
	memcpy(&sin.sin_addr, h->h_addr, 4);
	sin.sin_port = htons((unsigned short)port);
	int result=connect(sok, (sockaddr *)&sin, sizeof(sin));
	if (result!=0)
	{
		std::string errmsg = strerror(errno);
		printf("connection failed (%s)", errmsg.c_str());
		throw std::runtime_error("connection failed ("+errmsg+")");
	}

	return sok;
}


static std::string receive(int sok)
{
	char buf[65536];
	int len=recv(sok, buf, 65536, 0);
	if (len<=0)
	{
		std::cout << "ERROR: recv failed\n" << std::flush;
		quit=true;
		return "";
	}
	else
		return std::string(buf, buf+len);
}

static void process_receive(std::string &buf)
{
	boost::algorithm::replace_all(buf, "\r", "");

	std::string::size_type enter;
	while (enter=buf.find('\n'), enter!=std::string::npos)
	{
		std::string line=buf.substr(0, enter);
		buf.erase(0, enter+1);
		threadlog() << "recv: \"" << line << "\"";
		interpret(line);
	}
}  


std::vector<std::string> arg;

int main(int argc, char *argv[])
{
	for (int n=0; n<argc; ++n) arg.push_back(argv[n]);

	setlinebuf(stdout); // make stdout linebuffered (otherwise, when writing to pipe, it will be block-buffered)

	try
	{
		int sok=connect_to_server(g_config.get_server(), g_config.get_port());

		create_send_thread(sok);

		sendstr_prio(std::string("pass somepass\nnick ")+g_config.get_nick()+"\nuser "+g_config.get_nick()+" b c d\n");

		::signal(SIGINT, sighandler);

		std::string recv_buf;
		while (!quit)
		{
			pollfd polls[1];
			polls[0].fd=sok; polls[0].events=POLLIN|POLLPRI; polls[0].revents=0;
			int n=poll(polls, 1, 1000/*ms*/);
			if (n<0 && errno==EINTR)
				continue;
			else if (n<0)
			{ // error
				int e=errno;
				char buf[1024];
				if (strerror_r(e, buf, 1024)!=0)
					strcpy(buf, "no message");
				std::cout << "poll failed, " << e << ", " << buf << "\n" << std::flush;
			}
			else if (n==0)
			{ // timeout
			}
			else if (polls[0].revents&(POLLERR|POLLHUP|POLLNVAL))
			{
				std::cout << "something happened to the socked, revents=" << polls[0].revents << ", doei!\n";
				quit=true;
			}
			else if (polls[0].revents&(POLLIN|POLLPRI))
			{ // something to receive on sok
				recv_buf+=receive(sok);
				process_receive(recv_buf);
			}

		}
		std::cout << "\n------------------------------------------------------------------------\n";
		std::cout << "exit't main while(quit=" << quit << "), continuing to quit\n" << std::flush;
		std::cout << "------------------------------------------------------------------------\n";

		py_handler_t::instance().destruct();

	}
	catch(const std::exception &e)
	{
		printf("terminated through exception: %s\n", e.what());
		return(-1);
	}
	catch(...)
	{
		printf("terminated through exception\n");
		return(-1);
	}
}


void interpret(const std::string &input)
{
  std::string sender;
  std::string email;
	std::string remainder=input;
  if (input[0]==':')
  { // extract the sender nick and email (":nick!email ")
		std::string::size_type l=input.find_first_of(' ');
    sender=input.substr(1,l);
		remainder=input.substr((l==std::string::npos?l:l+1));

    l=sender.find_first_of('!');
    if (l!=sender.npos)
    {
      email=sender.substr(l+1);
      sender.erase(l);
    }
  }
	// extract the command
	std::string::size_type l=remainder.find_first_of(' ');
	std::string command=remainder.substr(0, l);
	std::string params=remainder.substr((l==std::string::npos?l:l+1));

  //printf("interpret(\"%s\", \"%s\", \"%s\")\n", sender.c_str(), command.c_str(), params.c_str());
 
	std::string channel = g_config.get_channel();
	std::string::size_type spacepos = channel.find(' ');
	if (spacepos != std::string::npos)
		channel.erase(spacepos, std::string::npos);
  if (command=="PING")
  {
    sendstr_prio(std::string("PONG ")+params);
  }
  /*else if ((command=="NICK")&&(sender==g_config.get_nick()))
  {
    if (!params.empty())
    {
			std::string pietnick=params;
      if (pietnick[0]==':') pietnick.erase(0,1);
      printf("NICKCHANGE!\n");
      send(":%s PRIVMSG %s :server roept dat ik nu %s heet, het zal wel\n", pietnick.c_str(), channel.c_str(), pietnick.c_str());
			g_config.set_nick(pietnick);
    }
  }
  else if (command=="NICK")
  {
    std::string newnick=params;
    if (newnick[0]==':') newnick.erase(0,1);

    int auth=piet_db_get("SELECT auth FROM auth where name=\""+sender+"\"", -5);
    int otherauth=piet_db_get("SELECT auth FROM auth where name=\""+newnick+"\"", -5);
    printf("DEBUG: \"%s\"(%d) is ge-renick\'t naar \"%s\"(%d)\n", sender.c_str(), auth, newnick.c_str(), otherauth);

		piet_db_set("REPLACE INTO auth(name,auth) VALUES(\""+sender+"\","+
				boost::lexical_cast<std::string>(otherauth)+")");
		piet_db_set("REPLACE INTO auth(name,auth) VALUES(\""+newnick+"\","+
				boost::lexical_cast<std::string>(auth)+")");

    if (auth>otherauth)
      send(":%s PRIVMSG %s :authenticatie %d nu naar %s overgezet, %s heeft 't niet meer nodig lijkt me\n", g_config.get_nick().c_str(), channel.c_str(), auth, newnick.c_str(), sender.c_str());
    else if ((auth<otherauth)&&(auth>0))
      send(":%s PRIVMSG %s :authenticatie %d nu naar %s overgezet, niet nickchangen om hogere auth te krijgen\n", g_config.get_nick().c_str(), channel.c_str(), auth, newnick.c_str(), sender.c_str());
  }*/
  else if (command=="433")
  { // recv: ":irc.nl.uu.net 433 piet simon :Nickname is already in use."
    send(":%s PRIVMSG %s :server roept dat die naam al in gebruik is!\n", g_config.get_nick().c_str(), channel.c_str());
  }
  else if (command=="432")
  {
    send(":%s PRIVMSG %s :server roept dat ik een ongeldige nick probeer te gebruiken!\n", g_config.get_nick().c_str(), channel.c_str());
  }
  else if (command=="422" || command=="376")
  {
    if (g_config.get_channel_key().empty())
      send(":%s JOIN %s\n", g_config.get_nick().c_str(), g_config.get_channel().c_str());
    else
      send(":%s JOIN %s %s\n", g_config.get_nick().c_str(), g_config.get_channel().c_str(), g_config.get_channel_key().c_str());
  }
  else if (command=="PRIVMSG")
  {
    std::string chan;
    { // extract the sending channel
			std::string::size_type l=params.find_first_of(' ');
      if (l!=params.npos)
      {
        chan=params.substr(0, l);
        params.erase(0,l+1);
      }
    }
    { // extract the message
			std::string::size_type l=params.find_first_of(':');
      if (l!=params.npos)
        params.erase(0, l+1);
    }
    
    Feedback(sender, Authenticate(sender, email), chan, params);
  }
  else
  {
    Feedback(sender, Authenticate(sender, email), channel, (g_config.get_nick()+": SERVER "+command+" "+params));
  }
}

int Authenticate(const std::string &nick, const std::string &email)
{
  return piet_db_get("SELECT auth FROM auth where name=\""+nick+"\"", -5);
}

