#include "piet_py_handler.h"
#include "privmsg_and_log.h"
#include "bot.h"
#include "sender.h"
#include "piet_db.h"
#include "pietconnection.h"
#include <signal.h>
#include <iostream>

boost::shared_ptr<pietconnection_t> g_socket;
bool g_restart = false;

void interpret(const std::string &input);

void sighandler(int sig)
{
	quit();
}

int main(int argc, char *argv[])
{
	setlinebuf(stdout); // make stdout linebuffered (otherwise, when writing to pipe, it will be block-buffered)

	try
	{
		g_socket.reset(new pietconnection_t(g_config.get_server(), to_str(g_config.get_port())));
		sendstr("pass somepass\n", false);
		sendstr("nick " + g_config.get_nick() + "\n", false);
		sendstr("user " + g_config.get_nick() + " b c d\n", false);

		::signal(SIGINT, sighandler);

		g_socket->run();

		std::cout << "\n------------------------\n";
		std::cout << "Dropped out of main loop\n" << std::flush;
		std::cout << "------------------------\n";

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

	if (g_restart)
	{
		std::vector<const char *> arg(argv+0, argv+argc);
		arg.push_back(NULL);
		threadlog() << "restarting " << arg[0];
		int err = execlp(arg[0], arg[0], (char *)NULL);
		if (err==-1)
		{ // this point can only be reached by an error
			perror("failed to restart");
		}
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
		sendstr_prio("PONG " + params);
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

