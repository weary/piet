#!/usr/bin/python

import sys,string,random,re,os,time;

nick = string.strip(sys.stdin.readline());
auth = int(string.strip(sys.stdin.readline()));
channel = string.strip(sys.stdin.readline());
msg = string.strip(sys.stdin.readline());

params = string.split(msg);
if (len(params)>=1):
  if ((params[0]=="JOIN") and (nick!="piet")):
    print "ik noteer: "+nick+" is wakker geworden om "+time.strftime("%H:%M %d-%m-%Y");
  elif ((params[0]=="PART") or (params[0]=="QUIT")):
    print "ik noteer: "+nick+" gaat slapen om "+time.strftime("%H:%M %d-%m-%Y");
