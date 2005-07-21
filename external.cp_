
#include <unistd.h>
#include <stdio.h>
#include <sys/wait.h>
#include "bot.h"

pthreadlist plist;

void sendlines(const char *channel, char *line, int len)
{
  line[len]=0;
  //printf("%s\n", line);
  char *a=line;
  while (a)
  {
    char *b=a;
    a=strchr(a, '\n');
    if (a) a++[0]=0;
    if (strncmp(b, "NICK ", 5)==0)
      send(":%s NICK :%s\n", g_config.get_nick().c_str(), b+5);
    else
      send(":%s PRIVMSG %s :%s\n", g_config.get_nick().c_str(), channel, b);
  }
}

void *external(void *p);

void External(const char *channel, const char *cmd, const char *input)
{
  tthread_data *p=new tthread_data;
  p->channel=channel;
  p->cmd=cmd;
  p->input=input;
  p->ready=false;
  p->kill_after=time(NULL)+600;

  int result=pthread_create(&(p->thread), NULL, external, p);
  if (result)
  {
    printf("ERROR: failed to create thread, error code %d\n", result);
    delete(p); p=NULL;
    return;
  }
  plist.push_back(p);
}

void *external(void *p)
{
  tthread_data *p2=(tthread_data *)p;
  const char *channel=p2->channel.c_str();
  const char *cmd=p2->cmd.c_str();
  const char *input=p2->input.c_str();

  {
    std::string input2=unenter(std::string(input));
    printf("ext: started (\"%s\", \"%.20s\", \"%.20s\")\n", channel, cmd, input2.c_str());
  }
	/*  Define int arrays to ref pipes */
	int stdin_pipe[2];
	int stdout_pipe[2];
	int stderr_pipe[2];

	/* Create pipes to read from and write too */
	if ((pipe(stdin_pipe) == 0) && (pipe(stdout_pipe) == 0) && (pipe(stderr_pipe) == 0))
	{
		int fork_result = fork();
		if (fork_result == -1)
		{
			printf("ERROR: Fork Failure\n");
			return(false);
		}
		else if (fork_result == 0) // child
		{
			/* Close the Child process' STDIN */
			close(0);
			close(1);
			close(2);
			dup(stdin_pipe[0]);
			dup(stdout_pipe[1]);
			dup(stderr_pipe[1]);
			close(stdin_pipe[0]);
			close(stdin_pipe[1]);
			close(stdout_pipe[0]);
			close(stdout_pipe[1]);
			close(stderr_pipe[0]);
			close(stderr_pipe[1]);

                        execlp("bash", "bash", "-c", cmd, 0);
			printf("ERROR: Exec failed\n"); // if this is executed, the execlp failed
		}
		else // parent
		{
                        write(stdin_pipe[1], input, strlen(input));
			/* Close STDIN for read & write and close STDERR for write */
			close(stdin_pipe[0]);
			close(stdin_pipe[1]);
			close(stderr_pipe[1]);
			
                        close(stdout_pipe[1]);  // Close the write end of STDOUT
			
			char line[1024];
			int line_len;
                        bool fin1=false;
                        bool fin2=false;
                        while ((!fin1)||(!fin2))
			{
                          line_len=read(stderr_pipe[0],line,1023);
                          fin2=(line_len==0);
                          if (!fin2) sendlines(channel, line, line_len);

                          line_len=read(stdout_pipe[0],line,1023);
        fin1=(line_len==0);
        if (!fin1) sendlines(channel, line, line_len);
      }

			close(stderr_pipe[0]);  // Close the read end of STDERR
			close(stdout_pipe[0]); // Close STDOUT for reading
      waitpid(fork_result, NULL, 0);
    }
  }
  p2->ready=true;
  {
    std::string input2=unenter(std::string(input));
    printf("ext: finished (\"%s\", \"%.20s\", \"%.20s\")\n", channel, cmd, input2.c_str());
  }
  return(NULL);
}

