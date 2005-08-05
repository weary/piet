

//#include <unistd.h>
#include "python_handler.h"
#include "bot.h"
#include "sender.h"
#include "lua_if.h"
#include "passwd.h"
#include <boost/algorithm/string/replace.hpp>
#include <boost/algorithm/string/trim.hpp>
#include <boost/format.hpp>
#include <crypt.h>
#include <netdb.h>
#include <netinet/in.h>
#include <stdarg.h>
#include <sys/socket.h>
#include <sys/types.h>

//typedef std::map<std::string, int> tauth_map;
//extern tauth_map auth_map;
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
//#define COM_AUTH 13
#define COM_BUSY_ASK 14
#define COM_RENICK 15
#define COM_OPME 16
#define COM_BESILENT 17
#define COM_SILENT 18
#define COM_UNSILENT 19
#define COM_JOINME 20
#define COM_JOINME_NOAUTH 21
#define COM_SERVER 22
#define COM_RELOADLUA 24

struct scommand
{
  const char *name;
  int command;
  int auth;
};

const scommand commands[]= {
{ "stop",        COM_QUIT,  1000 },
{ "sterf",       COM_QUIT,  1000 },
{ "donder op",   COM_QUIT,  1000 },
{ "herstart",    COM_RESTART, 1000 },
{ "herlaars",    COM_RESTART, 1000 },
{ "ga weg",      COM_LEAVE, 1000 },
{ "ga weg van ", COM_LEAVE, 1000 },
{ "kom bij ",    COM_JOIN,  1000 },
{ "\001PING",    COM_CTCPPING, 100 },
{ "kop dicht",   COM_SHUTUP,1000 },
{ "koffie?",     COM_BUSY_ASK, 121},
//{ "auth",        COM_AUTH, -2500 },
{ "je heet nu ", COM_RENICK, 200 },
{ "opme",        COM_OPME,  150 },
{ "wees stil",   COM_BESILENT, 1000 },
{ "stil?",       COM_SILENT, 1000 },
{ "praat maar",  COM_UNSILENT, 1000 },
{ "lees lua",    COM_RELOADLUA, 1000 },
{ "SERVER",      COM_SERVER, 0 }
};


void Feedback(const std::string &nick, int auth, const std::string &channel_in, const std::string &msg_in)
{
  std::string msg=msg_in;
  std::string channel=channel_in;
  printf("Feedback, processing (\"%s\", %d, \"%s\", \"%s\")\n", nick.c_str(), auth, channel.c_str(), msg.c_str());
  
  // feedback kan 2 vormen hebben, persoonlijk, herkenbaar aan:
  //   1. op een kanaal: "NICK: zeg hallo"
  //   2. rechtstreeks: "zeg hallo"
  // of onpersoonlijk, alle andere gevallen op een kanaal
  bool on_channel=(channel!=g_config.get_nick());
  bool personal=!on_channel;
  if (msg.substr(0, g_config.get_nick().length()+1)==(g_config.get_nick()+":"))
  {
    msg.erase(0, g_config.get_nick().length()+1);
    personal=true;
  }

  printf("DEBUG: nick = \"%s\", channel = \"%s\", on_channel = %s, personal = %s\n", nick.c_str(), channel.c_str(), (on_channel?"TRUE":"FALSE"), (personal?"TRUE":"FALSE"));
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
          printf("DEBUG: due to invalid backquote string is now \"%s\"\n", msg.c_str());
        }
        else if (*i==';')
        {
          *i=':';
          printf("DEBUG: due to invalid ; string is now \"%s\"\n", msg.c_str());
        }
      }
    }
  }

  if (personal)
  {
		boost::algorithm::trim(msg);
    printf("This is a personal message, msg = \"%s\"\n", msg.c_str());

    // commando opzoeken in de tabel
    int com_index=-1;
    std::string params;
    for (int i=0; (i<(int)(sizeof(commands)/sizeof(scommand))) && (com_index==-1); i++)
    {
      if (strncasecmp(msg.c_str(), commands[i].name, strlen(commands[i].name))==0)
      {
        com_index=i;
        params=msg.c_str()+strlen(commands[i].name);
      }
    }
		boost::algorithm::trim(params);

    // it is a build in command
    if ((com_index>=0)&&(auth>=commands[com_index].auth))
    {
			std::cout << "Command: \"" << commands[com_index].name << "\", Params: \"" << params << "\"\n";
    
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
              send(":%s PRIVMSG %s :ehm %s, je bent vergeten een channel op te geven\n", g_config.get_nick().c_str(), channel.c_str(), nick.c_str());
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
            send(":%s PRIVMSG %s :ok %s\n", g_config.get_nick().c_str(), channel.c_str(), nick.c_str());
          }
          break;
        case(COM_BESILENT):
          {
            silent_mode=true;
            send(":%s PRIVMSG %s :ok %s\n", g_config.get_nick().c_str(), channel.c_str(), nick.c_str());
          }
          break;
        case(COM_SILENT):
          {
            send(":%s PRIVMSG %s :ik probeer me %sstil te houden\n", g_config.get_nick().c_str(), channel.c_str(), (silent_mode?"":"niet "));
          }
          break;
        case(COM_UNSILENT):
          {
            silent_mode=false;
            send(":%s PRIVMSG %s :bladiebladiebladiebla\n", g_config.get_nick().c_str(), channel.c_str());
          }
          break;
        case(COM_BUSY_ASK):
          {
						std::list<std::string> threads=python_handler::instance().threadlist();
            if (threads.size()==0)
              send(":%s PRIVMSG %s :ja, koffie is goed\n", g_config.get_nick().c_str(), channel.c_str());
            else
            {
              std::ostringstream res;
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
							std::cout << "BUSY_ASK: " << res.str();
              send(":%s PRIVMSG %s :%s\n", g_config.get_nick().c_str(), channel.c_str(), res.str().c_str());
            }
          }
          break;
        case(COM_RENICK):
          {
            send(":%s PRIVMSG %s :ik zal de server eens vragen of dat mag\n", g_config.get_nick().c_str(), channel.c_str());
            send(":%s NICK :%s\n", g_config.get_nick().c_str(), params.c_str());
          }
          break;
        case(COM_OPME):
          {
            send(":%s MODE %s +o %s", g_config.get_nick().c_str(), channel.c_str(), nick.c_str());
            send(":%s PRIVMSG %s :hoezo? ben ik dan operator ofzo? kan je dat zelf niet?\n", g_config.get_nick().c_str(), channel.c_str());
          }
          break;
        case(COM_RESTART):
          {
            send(":% QUIT :ben zo terug (hopelijk)\n", g_config.get_nick().c_str());
            restart=true;
          }
          break;

        case(COM_RELOADLUA):
          {
            send(":%s PRIVMSG %s :nou snel dan\n", g_config.get_nick().c_str(), channel.c_str());
						lua_inst.reset(new clua);
            send(":%s PRIVMSG %s :ok, gedaan\n", g_config.get_nick().c_str(), channel.c_str());
          }
          break;
        case(COM_SERVER):
          {
            msg=msg.substr(7);
						if (!lua_inst)
							send(":%s PRIVMSG %s :HelpHelpHelp, ik ben m'n instellingen kwijt!\n", g_config.get_nick().c_str(), channel.c_str());
						else
							lua_inst->server_msg(nick.c_str(), auth, channel.c_str(), msg.c_str());
          }
	  break;
        /*case(COM_AUTH):
          {
            int localauth=auth;
            int newauth=0;
            char nick_[20]; nick_[0]=0;
            char pwd_[20]; pwd_[0]=0;
            int val=sscanf(params.c_str(), "%d %20s %20s", &newauth, nick_, pwd_);
            if (newauth>1500) newauth=1500;
            if (newauth<-1500) newauth=-1500;

            const char *encrypted="<lege string>";
            bool passok=false;
            if (val==3)
            {
              encrypted=crypt(pwd_, "AB");
              printf("AUTH: encrypted ww = %s\n", encrypted);
              for (int i=0; i<botpasssize; i++)
              {
                if ((botpass[i].auth>localauth) && (strcmp(encrypted, botpass[i].pass)==0))
                {
                  localauth=botpass[i].auth;
                  passok=true;
                }
              }
            }

            if (((val==2)||(val==3)) && (newauth<=localauth) && (localauth>=auth_map[nick_]))
            {
              auth_map[nick_]=newauth;
              send(":%s PRIVMSG %s :ok, %s heeft nu authenticatieniveau %d\n", g_config.get_nick().c_str(), channel.c_str(), nick_, auth_map[nick_]);
            }
            else if ((params.empty())&&(localauth>=0))
            {
              tauth_map::const_iterator i=auth_map.begin();
              bool first=true;
              std::string result;
              while (i!=auth_map.end())
              {
                if ((*i).second!=0)
	              {
                  result=(boost::format("%1%%2%%3%%4%%5%%6%") % result % (first?"(":", (") % (*i).first % ", " % ((*i).second) % ")").str();
                  first=false;
                }
                i++;
              }
              if (result.empty())
                send(":%s PRIVMSG %s :ik ken helemaal niemand!", g_config.get_nick().c_str(), channel.c_str());
              else
                send(":%s PRIVMSG %s :bij mij zijn bekend: %s", g_config.get_nick().c_str(), channel.c_str(), result.c_str());
            }
            else if (localauth>=0)
            {
              if ((val==2)||((val==3)&&(passok==true)))
              {
                send(":%s PRIVMSG %s :niet goed, mag niet\n", g_config.get_nick().c_str(), channel.c_str());
                send(":%s PRIVMSG %s :%s: je mag tot level %d geven\n", g_config.get_nick().c_str(), channel.c_str(), nick.c_str(), localauth);
              }
              else if (val==3)
                send(":%s PRIVMSG %s :niet goed, mag niet, wachtwoordfout in \"%s\" denk ik\n", g_config.get_nick().c_str(), channel.c_str(), encrypted);
              else
                send(":%s PRIVMSG %s :niet goed, mag niet.\n", g_config.get_nick().c_str(), channel.c_str());
            }
            else
              printf("WARNING: %s heeft localauth %d en krijgt dus geen feedback\n", nick.c_str(), localauth);
          }
          break;*/
      }
    }
    else
		{
			python_cmd cmd(channel, "do_command", 4);
			cmd << nick << auth << channel << msg;
			python_handler::instance().read_and_exec(channel, "command.py", cmd);
		}
  } // end personal
  else if ((sendqueue_size()==0)&&(silent_mode==false))
	{
		python_cmd cmd(channel, "do_react", 4);
		cmd << channel << nick << g_config.get_nick() << msg;
		python_handler::instance().read_and_exec(channel, "react.py", cmd);
	}
}

