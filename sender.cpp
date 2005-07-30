

#include <pthread.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <netdb.h>
#include <stdarg.h>
#include <stdio.h>
#include <map>
#include "sender.h"
#include "bot.h"


typedef std::list<std::string> stringlist;
static stringlist send_list;
static pthread_mutex_t sendqueue_mutex = PTHREAD_MUTEX_INITIALIZER;
static pthread_t sender_thread;

// the thread function..
static void *sender(void *data);

struct senderthread_data_t
{
	int _sok;
};

void create_send_thread(int sok)
{
  int result;
	senderthread_data_t *sd=new senderthread_data_t;
	sd->_sok=sok;
  result=pthread_create(&sender_thread, NULL, sender, sd);
  if (result)
  {
    printf("failed to create sender thread, error code %d\n", result);
    throw;
  }
  printf("Send thread created\n");
}

void join_send_thread()
{
	pthread_join(sender_thread, NULL);
}


// put a header+textline in the queue, lines should be <=450 chars
static void add_to_sendlist(const std::string header, const std::string textline, bool high_prio)
{
  printf("SEND: add_to_sendlist(\"%.45s\", \"%.45s\", %s)\n", unenter(header).c_str(), unenter(textline).c_str(), (high_prio?"TRUE":"FALSE"));

  if (textline.empty()) return;

  pthread_mutex_lock(&sendqueue_mutex);
  if (high_prio)
    send_list.push_front(header+textline+'\n');
  else
    send_list.push_back(header+textline+'\n');
  pthread_mutex_unlock(&sendqueue_mutex);
}

// split text into 450-character pieces and add it to the send queue
// header and high_prio are just passed through
static void send_one_line(const std::string header, std::string text, bool high_prio)
{
  printf("SEND: send_one_line(\"%.45s\", \"%.45s\", %s)\n", unenter(header).c_str(), unenter(text).c_str(), (high_prio?"TRUE":"FALSE"));

  while (!text.empty())
  {
    unsigned int sendlen=text.length();
    if (sendlen>450)
    {
      sendlen=text.find_last_of(' ', 450);
      if ((sendlen<350)||(sendlen==std::string::npos)) sendlen=450;
    }
    add_to_sendlist(header, text.substr(0,sendlen), high_prio);
    text.erase(0, sendlen);
    if ((!text.empty())&&(text[0]==' ')) text.erase(0, 0);
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
  printf("SEND: send(\"%s\", %s)\n", unenter(msg).c_str(), (high_prio?"TRUE":"FALSE"));

  std::string header;
  std::string alltext;
  { // extract header
    unsigned int p=msg.find_first_of(':', 1);
    if (p!=std::string::npos)
      header=msg.substr(0,p+1), alltext=msg.substr(p+1);
    else
      header.erase(), alltext=msg;
  }

  while (!alltext.empty())
  {
    unsigned int enterpos=alltext.find_first_of('\n');
    if (enterpos==std::string::npos)
      send_one_line(header, alltext, high_prio), alltext.erase();
    else
      send_one_line(header, alltext.substr(0, enterpos), high_prio), alltext.erase(0, enterpos+1);
  }
}

// call send, with normal priority
void send(const char *fmt, ...)
{
  va_list ap; va_start(ap, fmt);
  char *p=new char[1024];
  int n = vsnprintf(p, 1024, fmt, ap);
  if ((n<0)||(n>1023))
  {
    delete(p); p=new char[n+1];
    n = vsnprintf(p, n+1, fmt, ap);
  }
  va_end(ap);
  sendstr(std::string(p), false);
  delete(p);
}


// separate thread that checks the send queue
static void *sender(void *vsi)
{
	senderthread_data_t *td=reinterpret_cast<senderthread_data_t *>(vsi);
	int sok=td->_sok;
	delete(td); // right, can't forget to delete that anymore :)

  int counter=8;
  pthread_mutex_init(&sendqueue_mutex, NULL);
  while (!quit)
  {
    sleep(1);
    if (counter<8) 
		  ++counter;

    pthread_mutex_lock(&sendqueue_mutex);
    while ((send_list.size()>0) && (counter>=2))
    {
      send(sok, send_list.front().c_str(), send_list.front().length(), 0);
      counter-=2;
      send_list.pop_front();
    }
    pthread_mutex_unlock(&sendqueue_mutex);
  }
  pthread_mutex_destroy(&sendqueue_mutex);
  return(NULL);
}


// remove all pending items from send-queue
void sender_flush()
{
  pthread_mutex_lock(&sendqueue_mutex);
  send_list.clear();
  pthread_mutex_unlock(&sendqueue_mutex);
}

// return how many messages remain unsend
unsigned int sendqueue_size()
{
  pthread_mutex_lock(&sendqueue_mutex);

  unsigned int r=send_list.size();
  pthread_mutex_unlock(&sendqueue_mutex);
  return(r);
}

