
#include <pthread.h>
#include <stdio.h>
#include <map>
#include <string>
#include <list>

//#define INITIALNICK "rarepiet"

//#define SERVER "irc.xs4all.nl"
//#define SERVER "irc.snt.utwente.nl"
//#define SERVER "irc.nl.uu.net"
//#define SERVER "130.89.169.34" // groentje
//#define SERVER "eris.ircnet.org"

//#define CHANNEL "#piettest"
//#define CHANNEL "#\22a\22e_mensen"

//#define SERVICE "ircd_groentje"
//#define SERVICE "ircd"

class c_piet_config // global variable g_config can be used to access this one
{
	public:
		c_piet_config();
		~c_piet_config() {}

		// initial configuration
		const std::string &get_server() { return _server; }
		const std::string &get_service() { return _service; }

		const std::string &get_initial_nick() { return _initial_nick; }
		const std::string &get_channel() { return _channel; }

		// changing configuration
		const std::string &get_nick() { return _nick; }
		void set_nick(const std::string &nick) { _nick=nick; }

	protected:
		std::string _server;
		std::string _service;
		std::string _initial_nick;
		std::string _channel;

		std::string _nick;
};
extern c_piet_config g_config;

//#define BOGUS
inline std::string unenter(const std::string a)
{
  std::string input=a;
  std::string::iterator i=input.begin();
  while (i!=input.end())
  {
    if (*i=='\n') *i=':'; else i++;
  }
  return(input);
}

struct tthread_data
{
  pthread_t thread;
  time_t kill_after;
  bool ready;

  // voor de thread
  std::string channel;
  std::string cmd;
  std::string input;
};

typedef std::list<tthread_data *> pthreadlist;

extern bool initialising;
extern bool quit;
extern int sok;
extern pthreadlist plist;
//extern std::string pietnick;

void *sender(void *);
void *receiver(void *);
void *nieuws(void *p);

void interpret(const char *);

//void send(const char *fmt, ...);
//void send_prio(const char *fmt, ...);
int Authenticate(const std::string &nick, const std::string &email);
void Feedback(const std::string &nick, int auth, const std::string &channel, const std::string &msg);
void External(const char *channel, const char *cmd, const char *input);
void collect_garbage();
void killall();

void send(const char *fmt, ...);
void sendstr(const std::string msg, bool high_prio);
inline void sendstr_prio(const std::string msg) { sendstr(msg, true); }
void sender_flush();
unsigned int sendqueue_size();

