
#include "piet_py_handler.h"
#include "privmsg_and_log.h"
#include "bot.h"
#include "sender.h"
#include <boost/algorithm/string/replace.hpp>
#include <boost/algorithm/string/trim.hpp>
#include <boost/algorithm/string/predicate.hpp>
#include <boost/format.hpp>
#include <crypt.h>
#include <netdb.h>
#include <netinet/in.h>
#include <stdarg.h>
#include <sys/socket.h>
#include <iostream>
#include <sstream>
#include <sys/types.h>

extern bool restart;
bool silent_mode=false;

using boost::format;

#define COM_INVALID -1
#define COM_QUIT 0
#define COM_RESTART 23
#define COM_LEAVE 1
#define COM_JOIN 2
#define COM_CTCPPING 51
#define COM_NEWS 11
#define COM_SHUTUP 12
#define COM_BUSY_ASK 14
//#define COM_RENICK 15
#define COM_BESILENT 17
#define COM_SILENT 18
#define COM_UNSILENT 19
#define COM_JOINME 20
#define COM_JOINME_NOAUTH 21
#define COM_SERVER 22

struct scommand
{
  const char *name;
  int command;
  int auth;
};

const scommand commands[]= {
{ "sterf",       COM_QUIT,  1000 },
{ "donder op",   COM_QUIT,  1000 },
{ "herstart",    COM_RESTART, 1000 },
{ "herlaars",    COM_RESTART, 1000 },
{ "ga weg",      COM_LEAVE, 1000 },
{ "ga weg van ", COM_LEAVE, 1000 },
{ "kom bij ",    COM_JOIN,  1000 },
{ "\001PING",    COM_CTCPPING, 100 },
{ "stop",        COM_SHUTUP, 1000 },
{ "kop dicht",   COM_SHUTUP, 1000 },
{ "stfu",   COM_SHUTUP, 1000 },
{ "koffie?",     COM_BUSY_ASK, 121},
//{ "je heet nu ", COM_RENICK, 200 },
{ "wees stil",   COM_BESILENT, 1000 },
{ "stil?",       COM_SILENT, 1000 },
{ "praat maar",  COM_UNSILENT, 1000 },
{ "SERVER",      COM_SERVER, -5 }
};


void Feedback(const std::string &nick, int auth, const std::string &channel_in, const std::string &msg_in)
{
	using boost::algorithm::iequals;
  std::string msg=msg_in;
  std::string channel=channel_in;
  threadlog() << "Feedback, processing (" << nick << ", " << auth << ", " << channel_in << ", \"" << msg_in << "\")";
  
  // feedback kan 2 vormen hebben, persoonlijk, herkenbaar aan:
  //   1. op een kanaal: "NICK: zeg hallo"
  //   2. rechtstreeks: "zeg hallo"
  // of onpersoonlijk, alle andere gevallen op een kanaal
  const std::string pietnick=g_config.get_nick();
  bool on_channel=(channel!=pietnick);
  bool personal=!on_channel;
	std::string nickseparators = ":,> ";
	std::string::iterator pos = std::find_first_of(msg.begin(), msg.end(),
			nickseparators.begin(), nickseparators.end());
	if (pos != msg.end())
	{
		std::string testnick(msg.begin(), pos);
		if (iequals(testnick, pietnick) || iequals(testnick, "piet"))
		{
			++pos;
			msg.erase(msg.begin(), pos);
			personal = true;
		}
	}

  //threadlog() << "DEBUG: nick = \"" << nick << "\", channel = \"" << channel << "\", "
  //"on_channel = " << (on_channel?"TRUE":"FALSE") << ", personal = " << (personal?"TRUE":"FALSE") << "\n";
  if (!on_channel)
  { // fix for correct return path
    channel=nick;
  }

  // remove ` and ;
  {
    if (auth<1200)
    {
      std::string::iterator i;
      for(i=msg.begin(); i!=msg.end(); i++)
      {
        if (*i=='`')
        {
          *i='\'';
          threadlog() << "DEBUG: due to invalid backquote string is now \"" << msg << "\"\n";
        }
        else if (*i==';')
        {
          *i=':';
          threadlog() << "DEBUG: due to invalid ; string is now \"" << msg << "\"\n";
        }
      }
    }
  }

  if (personal)
  {
		boost::algorithm::trim(msg);
		//threadlog() << "This is a personal message, msg = \"" << msg << "\"\n";

    // commando opzoeken in de tabel
    int com_index=-1;
    std::string params;
    for (int i=0; (i<(int)(sizeof(commands)/sizeof(scommand))) && (com_index==-1); ++i)
    {
			if (boost::algorithm::istarts_with(msg, commands[i].name))
      {
        com_index=i;
        params=msg.substr(strlen(commands[i].name));
      }
    }
		boost::algorithm::trim(params);

		if (com_index>=0)
			threadlog() << "command: \"" << commands[com_index].name << ", requires auth " << 
				commands[com_index].auth << ", you have " << auth << ", params: \"" << params << "\"\n";
    // it is a build in command
    if ((com_index>=0)&&(auth>=commands[com_index].auth))
    {
      switch(commands[com_index].command)
      {
        case(COM_QUIT):
          {
            if (params.empty())
						{
							if (commands[com_index].name==std::string("sterf"))
								send(":%s QUIT :helaas geen natuurlijke dood gestorven\n", g_config.get_nick().c_str());
							else
								send(":%s QUIT :off to a better life in oblivion\n", g_config.get_nick().c_str());
						}
            else 
              send(":%s QUIT :%s\n", g_config.get_nick().c_str(), params.c_str());
            break;
          }
        case(COM_LEAVE):
          {
            sendstr_prio(std::string(":")+g_config.get_nick()+" PART "+(params.empty()?channel:params));
            break;
          }
        case(COM_JOIN):
          {
            if (!params.empty())
              sendstr_prio(std::string(":")+g_config.get_nick()+" JOIN "+params);
            else
							privmsg(channel) << "ehm " << nick << ", je bent vergeten een channel op te geven";
            break;
          }
        case(COM_CTCPPING):
          {
            sendstr_prio(std::string(":")+g_config.get_nick()+" NOTICE "+channel+" :"+msg);
          }
          break;
        case(COM_SHUTUP):
          {
            sender_flush();
            privmsg(channel) << "ok " << nick;
          }
          break;
        case(COM_BESILENT):
          {
            silent_mode=true;
            privmsg(channel) << "ok " << nick;
          }
          break;
        case(COM_SILENT):
          {
            privmsg(channel) << "ik probeer me " << (silent_mode?"stil":"niet stil") << " te houden";
          }
          break;
        case(COM_UNSILENT):
          {
            silent_mode=false;
            privmsg(channel) << "bladiebladiebladiebla";
          }
          break;
        case(COM_BUSY_ASK):
          {
						std::list<std::string> threads = py_handler_t::instance().threadlist();
            if (threads.size()==0)
              privmsg(channel) << "ja, koffie is goed";
            else
            {
							privmsg res(channel);
							res << "hmm, ja, koffie, maare, nog ff [";
							std::list<std::string>::const_iterator i;
              bool first=true;
              for (i=threads.begin(); i!=threads.end(); ++i)
              {
								if (!first) res << ", ";
								res << *i;
                
                first=false;
              }
              res << "] afmaken, maar daarna koffie\n";
            }
          }
          break;
        /*case(COM_RENICK):
          {
            send(":%s PRIVMSG %s :ik zal de server eens vragen of dat mag\n", g_config.get_nick().c_str(), channel.c_str());
            send(":%s NICK :%s\n", g_config.get_nick().c_str(), params.c_str());
          }
          break;*/

				case(COM_RESTART):
          {
            send(":% QUIT :ben zo terug (hopelijk)\n", g_config.get_nick().c_str());
						while (sendqueue_size()) sleep(1);
						std::vector<const char *> arg2;
						for (std::vector<std::string>::const_iterator i=arg.begin(); i!=arg.end(); ++i)
							arg2.push_back(i->c_str());
						arg2.push_back(NULL);
						threadlog() << "restarting " << arg2[0];
						int err=execlp(arg2[0], arg2[0], (char *)NULL);
						if (err==-1) { // this point can only be reached by an error
							perror("failed to restart");
						}
						quit = true;
          }
          break;

        case(COM_SERVER):
          {
            msg=msg.substr(7);
						py_handler_t::instance().read_file_if_changed(channel, "server.py");
						py_handler_t::instance().exec(channel, nick, auth, "do_server", msg);
          }
	  break;
      }
    }
    else
		{
			py_handler_t::instance().read_file_if_changed(channel, "command.py");
			py_handler_t::instance().exec(channel, nick, auth, "do_command", msg);
		}
  } // end personal
  else if ((sendqueue_size()==0)&&(silent_mode==false))
	{
		py_handler_t::instance().read_file_if_changed(channel, "react.py");
		py_handler_t::instance().exec(channel, nick, auth, "do_react", msg);
	}
}

