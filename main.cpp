#include <unistd.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <netdb.h>
#include <stdarg.h>
#include <crypt.h>
#include <boost/format.hpp>
#include <errno.h>
#include "bot.h"
#include "passwd.h"
#include "lua_if.h"

using boost::format;

typedef std::map<std::string, int> tauth_map;
tauth_map auth_map;

pthread_t sender_thread;
pthread_t receiver_thread;
//pthread_t garbage_collector_thread;

//std::string pietnick = g_config.get_initial_nick();

int sok=0;

struct receiver_info
{
  int s;
};

bool initialising=true;
bool quit=false;
bool restart=false;


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
  
void create_threads(receiver_info *ri)
{
  int result;
  result=pthread_create(&sender_thread, NULL, sender, NULL);
  if (result)
  {
    printf("failed to create sender thread, error code %d\n", result);
    throw;
  }
  result=pthread_create(&receiver_thread, NULL, receiver, ri);
  if (result)
  {
    printf("failed to create receiver thread, error code %d\n", result);
    throw;
  }
  //result=pthread_create(&garbage_collector_thread, NULL, garbage_collector, NULL);
  //if (result) { printf("failed to create garbage collector thread, error code %d\n", result); return(-2); }
  printf("Threads created\n");
}



int main(int argc, char *argv[])
{
  try {
		lua_inst.reset(new clua);

  //auth_map[std::string("piet")]=-10;
  auth_map[std::string("weary")]=1200;
  auth_map[std::string("Semyon")]=1000;
  auth_map[std::string("Socrates")]=1000;
  auth_map[std::string("Slaine")]=1000;
  auth_map[std::string("Groentje")]=1000;
  auth_map[std::string("Neighbour")]=1000;
  auth_map[std::string("neb")]=1000;
  auth_map[g_config.get_nick()]=150; // <-- om te zorgen dat ie zichzelf het auth systeem niet uitlegt
  auth_map[std::string("Bouncer")]=-1;

  receiver_info ri;

  create_threads(&ri);

#ifndef BOGUS
  sok=connect_to_server();
  ri.s=sok;
#endif
  
  initialising=false;

  sendstr_prio(std::string("pass somepass\nnick ")+g_config.get_nick()+"\nuser "+g_config.get_nick()+" b c d\n");
  sleep(30);

  send(":%s JOIN %s \22aa\22\n", g_config.get_nick().c_str(), g_config.get_channel().c_str());
  while (!quit)
  {
    sleep(30);
    collect_garbage();
  }
  printf("exit't main while, continuing to quit\n");
  
  killall();

  pthread_join(receiver_thread, NULL);
  pthread_join(sender_thread, NULL);
  //pthread_kill(garbage_collector_thread, 9);
  //pthread_join(garbage_collector_thread, NULL);
  
  if (restart)
  {
    printf("restarting %s\n", argv[0]);
    execlp(argv[0], "");
  }


  } catch(...) {
    printf("terminated through exception\n");
    return(-1);
  }
}

void *receiver(void *vri)
{
  while (initialising) sleep(1);

  receiver_info *ri=(receiver_info *)vri;
#ifdef BOGUS
  printf("receiver thread started in BOGUS mode\n");
#else // BOGUS
  printf("receiver thread started, using socket %d\n", ri->s);
  char buf[65536];
  char buf2[65536*2];
  
  int len,len2;
  len2=0;
  while(len=recv(ri->s, buf, 65536, 0),len>0)
  {
    memcpy(buf2+len2, buf, len);
    len2+=len;
    buf2[len2]=0;
    char *enter;
    while (enter=strchr(buf2, '\n'),((enter)||(len2>65536)))
    {
      if ((len2>65536)&&(!enter)) enter=buf2+65536;
      if (enter)
      {
        if ((enter>buf2)&&(enter[-1]==0xd)) enter[-1]=0;
        enter[0]=0;
        printf("recv: \"%s\"\n", buf2);
        fflush(stdout);
        interpret(buf2);
        strcpy(buf2, enter+1);
        len2=strlen(buf2);
      }
    }
  }
  quit=true;
#endif
  return(NULL);
}

std::string to_string(int a)
{
  char line[64];
  sprintf(line, "%d", a);
  return(std::string(line));
}

void interpret(const char *input)
{
  std::string sender;
  std::string email;
  std::string command;
  std::string params;
  if (input[0]==':')
  { // extract the sender nick and email (":nick!email ")
    sender=input+1;
    unsigned int l=sender.find_first_of(' ');
    if (l!=sender.npos)
    {
      sender.erase(l);
      input+=sender.length()+2;
    }
    l=sender.find_first_of('!');
    if (l!=sender.npos)
    {
      email=sender.substr(l+1);
      sender.erase(l);
    }
  }
  { // extract the command
    command=input;
    unsigned int l=command.find_first_of(' ');
    if (l!=sender.npos)
    {
      command.erase(l);
      input+=command.length()+1;
    }
  }
  { // put the remainer in params
    params=input;
  }

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

