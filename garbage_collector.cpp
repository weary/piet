
#include <unistd.h>
#include "bot.h"
#include <time.h>
#include <signal.h>

void collect_garbage()
{
  time_t t=time(NULL);

  printf("GC: sequence started, time is now %d (= %d:%d mod 3600)\n", (unsigned int)t, (((unsigned int)t) % 3600)/60, ((unsigned int)t) % 60);
  
  pthreadlist::iterator i=plist.begin();
  while (i!=plist.end())
  {
    {
      //time_t t1=(*i)->kill_after;
      printf("GC: checking %s(%.15s)\n", (*i)->cmd.c_str(), unenter((*i)->input).c_str());
      //printf("GC: - will be killed at %d (= %d:%d mod 3600)\n", (unsigned int)t1, (((unsigned int)t1) % 3600)/60, ((unsigned int)t1) % 60);
    }
    //if ((t > (*i)->kill_after) && ((*i)->ready==false))
    //{
    //  printf("GC: - kill %s(%.10s)\n", (*i)->cmd.c_str(), unenter((*i)->input).c_str());
    //  //pthread_kill((*i)->thread, SIGTERM);
    //  pthread_cancel((*i)->thread);
    //  printf("GC: - the deed is done\n");
    //  (*i)->ready=true;
    //  i++;
    //}
    //else 
    if((*i)->ready)
    {
      printf("GC: - removing %s(%.15s)\n", (*i)->cmd.c_str(), unenter((*i)->input).c_str());
      pthread_join((*i)->thread, NULL);
      delete(*i);
      i=plist.erase(i);
    }
    else
      i++;
  }
  printf("GC: finished\n");
}

void killall()
{
  // arg! shutdown! quick! killing spree!
  pthreadlist::const_iterator i=plist.begin();
  while (i!=plist.end())
  {
    pthread_kill((*i)->thread, 9);
    pthread_join((*i)->thread, NULL);
  }
  plist.clear();
}


