#!/usr/bin/python

import sys,string,random,re,os,time;
import piet;

def maketimestring(ut):
	try:
		minuten,seconden=int(ut/60),int(ut%60);
		uren,minuten=int(minuten/60),int(minuten%60);
		dagen,uren=int(uren/24),int(uren%24);

		result="";
		if (dagen>1):
			result=str(dagen)+" dagen, ";
		elif (dagen==1):
			result="1 dag, ";

		if (uren>1):
			result=result+str(uren)+" uren, ";
		elif (uren==1):
			result=result+"1 uur, ";

		if (minuten>1):
			result=result+str(minuten)+" minuten en ";
		elif (minuten==1):
			result=result+"1 minuut en ";

		if (seconden>1):
			result=result+str(seconden)+" seconden";
		elif (seconden==1):
			result=result+"1 seconde";
		else:
			result=result+"geen seconden";

	except:
		result="(nog steeds foutje in maketimestring, voor "+str(ut)+")";

	return result;

def doe_gemiddelde_offlinetijd(channel_, nick_, tu_):
	print("doe_gemiddelde_offlinetijd("+channel_+", "+nick_+", "+str(tu_)+")\n");
	# CREATE TABLE offline(channel string, nick string, tijd int)

	# CREATE TEMPORARY TABLE t(tijd int);
	# .import weary_offlinetijd.txt t
	# INSERT INTO offline SELECT "#^Ra^Re_mensen", "weary", tijd FROM t;
	# DROP TABLE t

	chan=string.lower(string.replace(channel_, '"', '\\"'));
	nick=string.lower(string.replace(nick_, '"', '\\"'));
	tijd=str(tu_);
	query='INSERT INTO offline VALUES("'+chan+'", "'+nick+'", '+tijd+')';
	piet.db(query);
	query='SELECT ROUND(AVG(tijd)) FROM offline WHERE channel="'+chan+'" and nick="'+nick+'"';
	if (tu_<3600):
		query+=" AND tijd<3600";
	elif (tu_<4*3600):
		query+=" AND tijd>=3600 AND tijd<4*3600";
	elif (tu_<20*3600):
		query+=" AND tijd>=4*3600 AND tijd<20*3600";
	else:
		query+=" AND tijd>=20*3600";
	avg=piet.db(query)[1][0];
	return int(avg);
	
	
def check_sleep_time(nick_, channel_, command_, msg_):
	print("check_sleep_time("+nick_+", "+channel_+", "+command_+", "+msg_+")\n");
	# CREATE TABLE logout(
	#		channel string, nick string, tijd int, reason string,
	#		primary key (channel,nick));

	chan=string.lower(string.replace(channel_, '"', '\\"'));
	nick=string.lower(string.replace(nick_, '"', '\\"'));
	if (command_ in ["PART", "QUIT"]):
		tijd=str(int(time.time()+0.5));
		reason=string.replace(msg_[5:], '"', '\\"');
		query='REPLACE INTO logout VALUES("'+chan+'", "'+nick+'", '+tijd+', "'+reason+'")';
		piet.db(query);
	elif (command_ in ["JOIN"]):
		try:
			where='WHERE channel="'+chan+'" and nick="'+nick+'"';
			tijd=piet.db('SELECT tijd FROM logout '+where)[1][0];
			piet.db('DELETE FROM logout '+where);
			tu=int(time.time()+0.5)-int(tijd);
			tu=tu;
			if (tu>0):
				result=maketimestring(tu);
				reply="Welkom "+nick+", dat was weer "+result;
				try:
					gemiddeld=doe_gemiddelde_offlinetijd(channel_, nick_, tu);
					reply+=", gemiddeld "+maketimestring(gemiddeld)+" nu";
				except:
					reply+=", geen gemiddelde";
				piet.send(channel_, reply+".\n");
			else:
				piet.send(channel_, "Blijkbaar is "+nick_+" aan het fietsen\n");
		except:
			piet.send(channel_, "Hee "+nick_+"!\n");

	

def do_server(nick_, auth_, channel_, msg_):
	print("do_server("+nick_+", "+str(auth_)+", "+channel_+", "+msg_+"\n");
	command=string.upper(string.split(msg_, ' ')[0]);
	if auth_>0 and (command in ["JOIN", "PART", "QUIT"]):
		check_sleep_time(nick_, channel_, command, msg_);
		


