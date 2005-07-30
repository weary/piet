#ifndef __PIET_SENDER_H__
#define __PIET_SENDER_H__

#include <string>

void create_send_thread(int sok);
void join_send_thread();

// remove all pending items from send-queue
void sender_flush();

// return how many messages remain unsend
unsigned int sendqueue_size();

// call send, with normal priority
void send(const char *fmt, ...);

// send a message with priority high if high_prio is true
// the message should be of the format:
//   msg := <header> <text> [\n <text>]
//   header := [:] <headertext>:   (header text may not contain :)
// from all text fields a list of lines is created with every line less-or-equal than 450 chars
// this list of text fields is then added to the send-queue
void sendstr(const std::string msg, bool high_prio);

inline void sendstr_prio(const std::string msg) { sendstr(msg, true); }

#endif // __PIET_SENDER_H__
