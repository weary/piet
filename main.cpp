#include "bot.h"
#include "lua_if.h"
#include "passwd.h"
#include "sender.h"
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
#include <unistd.h>

using boost::format;

typedef std::map<std::string, int> tauth_map;
tauth_map auth_map;

bool quit=false;
bool restart=false;

void interpret(const std::string &input);

// print the information in the sockaddr
void printsockaddr(const sockaddr *buf, unsigned int size)
{
  short family=buf->sa_family;
  u_short port=((u_short *)buf->sa_data)[0];
  port=ntohs(port);

  switch(family)
  {
    case(PF_INET): printf("ipv4 address"); break;
    case(PF_INET6): printf("ipv6 address"); break;
    default: printf("unknown address"); break;
  }
  printf(" for port %d, address:\n", port);

  const unsigned char *b=(const unsigned char *)buf->sa_data+sizeof(u_short);
  unsigned int s=size-sizeof(short)-sizeof(u_short);
  if (family==PF_INET) s-=8;
  if (family==PF_INET6) b+=4, s-=8;
  for (unsigned int i=0; i<s; i++)
  {
    printf(" %.2x", b[i]);
  }
  printf("\n");
}


int connect_to_server()
{
	std::string server=g_config.get_server();
	std::string service=g_config.get_service();
  int sok=socket(PF_INET, SOCK_STREAM, 0);
  printf("Got socket %d, looking up host \"%s\" for service \"%s\"\n",
			sok,
			server.c_str(),
			service.c_str());
  addrinfo *ainfo=NULL;
  {
    int result=getaddrinfo(server.c_str(), service.c_str(), NULL, &ainfo);
    if (result!=0)
    {
      printf("Could not find host!\n%s", gai_strerror(result));
      throw;
    }
  }

  { // try to connect to the addrinfo-thingy's
    addrinfo *ai=ainfo;
    int result=-1;
    while ((result!=0) && (ai!=NULL))
    {
      //u_short *portaddr=(u_short *)&(((sockaddr *)ai->ai_addr)->sa_data);
      //portaddr[0]=htons(5500);
      printsockaddr(ai->ai_addr, ai->ai_addrlen);
      result=connect(sok, ai->ai_addr, ai->ai_addrlen);
      if (result!=0)
      {
        printf("connection failed (%s)", strerror(errno));
        if (ai->ai_next)
        {
          printf(", advancing to next address");
          ai=ai->ai_next;
        }
        printf("\n");
      }
    }
    freeaddrinfo(ainfo);
    if (result!=0)
      throw;
    else
      printf("Ok, connection established\n");
  }
  return(sok);
}
  
static std::string receive(int sok)
{
	char buf[65536];
	int len=recv(sok, buf, 65536, 0);
	if (len<=0)
	{
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
		std::cout << "recv: \"" << line << "\"\n" << std::flush;
		interpret(line);
	}
}  



int main(int argc, char *argv[])
{
	try
	{
		lua_inst.reset(new clua);

		//auth_map[std::string("piet")]=-10;
		auth_map[std::string("weary")]=1200;
		auth_map[std::string("Semyon")]=1000;
		auth_map[std::string("Socrates")]=1000;
		auth_map[std::string("Slaine")]=1000;
		auth_map[std::string("Groentje")]=1000;
		auth_map[std::string("Neighbour")]=1000;
		auth_map[std::string("neb")]=1000;
		auth_map[std::string("chm")]=1000;
		auth_map[g_config.get_nick()]=150; // <-- om te zorgen dat ie zichzelf het auth systeem niet uitlegt
		auth_map[std::string("Bouncer")]=-1;

		int sok=connect_to_server();

		create_send_thread(sok);

		sendstr_prio(std::string("pass somepass\nnick ")+g_config.get_nick()+"\nuser "+g_config.get_nick()+" b c d\n");

		int garbagecollect_count=30;
		std::string recv_buf;
		while (!quit)
		{
			pollfd polls[1];
			polls[0].fd=sok; polls[0].events=POLLIN|POLLPRI; polls[0].revents=0;
			int n=poll(polls, 1, 1000/*ms*/);
			if (n<0)
			{ // error
				printf("poll failed\n"); quit=true;
			}
			else if (n==0)
			{ // timeout
			}
			else if (polls[0].revents&(POLLERR|POLLHUP|POLLNVAL))
			{
				std::cout << "something happened to the socked, revents=" << polls[0].revents << ", ignoring\n";
			}
			else if (polls[0].revents&(POLLIN|POLLPRI))
			{ // something to receive on sok
				recv_buf+=receive(sok);
				process_receive(recv_buf);
			}

			if (--garbagecollect_count==0)
			{
				collect_garbage();
				garbagecollect_count=30;
			}
		}
		printf("exit't main while, continuing to quit\n");

		killall();

		join_send_thread();

		if (restart)
		{
			std::string cmdline=argv[0];
			printf("restarting %s\n", cmdline.c_str());
			int err=execlp(cmdline.c_str(), "");
			if (err==-1) // this point can only be reached by an error
			{
				perror("failed to restart");
			}
		}

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
    unsigned int l=input.find_first_of(' ');
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
	unsigned int l=remainder.find_first_of(' ');
	std::string command=remainder.substr(0, l);
	std::string params=remainder.substr((l==std::string::npos?l:l+1));

  printf("interpret(\"%s\", \"%s\", \"%s\")\n", sender.c_str(), command.c_str(), params.c_str());
 
	std::string channel=g_config.get_channel();
  if (command=="PING")
  {
    sendstr_prio(std::string("PONG ")+params);
  }
  else if ((command=="NICK")&&(sender==g_config.get_nick()))
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

    int auth=auth_map[sender];
    int otherauth=auth_map[newnick];
    printf("DEBUG: \"%s\"(%d) is ge-renick\'t naar \"%s\"(%d)\n", sender.c_str(), auth, newnick.c_str(), otherauth);

    auth_map[sender]=otherauth;
    auth_map[newnick]=auth;
    if (auth>otherauth)
      send(":%s PRIVMSG %s :authenticatie %d nu naar %s overgezet, %s heeft 't niet meer nodig lijkt me\n", g_config.get_nick().c_str(), channel.c_str(), auth, newnick.c_str(), sender.c_str());
    else if ((auth<otherauth)&&(auth>0))
      send(":%s PRIVMSG %s :authenticatie %d nu naar %s overgezet, niet nickchangen om hogere auth te krijgen\n", g_config.get_nick().c_str(), channel.c_str(), auth, newnick.c_str(), sender.c_str());
  }
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
		send(":%s JOIN %s \22aa\22\n", g_config.get_nick().c_str(), g_config.get_channel().c_str());
	}
  else if (command=="PRIVMSG")
  {
    std::string chan;
    { // extract the sending channel
      unsigned int l=params.find_first_of(' ');
      if (l!=params.npos)
      {
        chan=params.substr(0, l);
        params.erase(0,l+1);
      }
    }
    { // extract the message
      unsigned int l=params.find_first_of(':');
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
  return(auth_map[nick]);
}

