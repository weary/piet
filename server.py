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

	chan=string.lower(string.replace(channel_, '"', '""'));
	nick=string.lower(string.replace(nick_, '"', '""'));
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
	
	
def check_sleep_time(nick_, auth_, channel_, command_, msg_):
	print("check_sleep_time("+nick_+", "+str(auth_)+", "+channel_+", "+command_+", "+msg_+")\n");
	# CREATE TABLE logout(
	#		channel string, nick string, tijd int, reason string,
	#		primary key (channel,nick));

	chan=string.lower(string.replace(channel_, '"', '""'));
	nick=string.lower(string.replace(nick_, '"', '""'));
	if (command_ in ["PART", "QUIT", "KICK"]):
		tijd=str(int(time.time()+0.5));
		reason=string.replace(msg_[5:], '"', '""');
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

def quitmsg_is_split(msg_):
	print("quitmsg_is_split("+msg_+")\n");
	return bool(re.match('^QUIT :[\w\.\*]+\.\w{2,3} [\w\.\*]+\.\w{2,3}$', msg_));

def check_netsplit(nick_, channel_, command_, msg_):
	print("check_netsplit("+nick_+", "+channel_+", "+command_+", "+msg_+"):\n");
	# CREATE TABLE netsplit(channel string,nick string, servers string, timeout int, PRIMARY KEY(channel,nick));

	NETSPLIT_TIMEOUT=3600; # seconds
	if (command_ in ["QUIT"]):
		if quitmsg_is_split(msg_):
			chan=string.lower(string.replace(channel_, '"', '""'));
			nick=string.lower(string.replace(nick_, '"', '""'));
			servers=string.replace(msg_[6:], '"', '""');
			tijd=str(int(time.time()+0.5)+NETSPLIT_TIMEOUT);
			query='REPLACE INTO netsplit VALUES("'+chan+'", "'+nick+'", "'+servers+'", '+tijd+')';
			piet.db(query);
			return True;
	elif (command_ in ["JOIN"]):
		chan=string.lower(string.replace(channel_, '"', '""'));
		nick=string.lower(string.replace(nick_, '"', '""'));
		tijd=int(time.time()+0.5);
		where='WHERE channel="'+chan+'" AND nick="'+nick+'" AND timeout>'+str(tijd);
		query='SELECT servers FROM netsplit '+where;

		ns=piet.db(query);
		if (not(ns)): return False;
		servers=ns[1][0];
		piet.db('DELETE FROM netsplit '+where);

		# others from same netsplit should return now within 30s -> restrict timeout
		query='REPLACE INTO netsplit ';
		query+='SELECT channel,nick,servers,MIN(timeout,'+str(tijd+30)+') '
		query+='FROM netsplit WHERE servers="'+servers+'"';
		piet.db(query);
		return True;

	return False;
		
def check_names(nick_, channel_, msg_):
	print("check_names("+nick_+", "+channel_+", "+msg_+")\n");
	nicks=set(string.split(msg_[string.find(msg_, ':')+1:], ' '));
	pietnick=piet.nick();
	if ('@'+pietnick in nicks):
		noop=[x for x in nicks if x[0]!='@'];
		if (not(noop)): return;
		qry="SELECT name FROM auth WHERE auth>=500 AND name IN ("+ \
				 string.join(['"'+x+'"' for x in noop], ',')+")";
		dbres=piet.db(qry);
		if (not(dbres)): return;
		print("dbres="+repr(dbres)+"\n");
		res=[x[0] for x in dbres[1:]];
		if (not(res)): return;
		if (len(res)==1):
			piet.send(channel_, "hup, een apenstaart voor "+res[0]+"\n");
		else:
			piet.send(channel_, "ho, hier moet even wat gefixed worden.\n");
		piet.op(channel_, res);
	else: # piet niet operator
		ops=[x[1:] for x in nicks if x[0]=='@'];
		if (not(ops)): return;
		myop=random.choice(ops);
		msg=random.choice(["mag ik een @?", "toe, doe eens een @?", \
				"ik wil graag je operatortje zijn, mag ik?", \
				"kijk, ik heb geen @. fix's?"]);
		piet.send(channel_, myop+": "+msg+"\n");

names_delayed_waiting=0
def check_names_delayed(channel_):
	global names_delayed_waiting;
	if (names_delayed_waiting>0):
		return;
	names_delayed_waiting=1;
	time.sleep(5);
	piet.names(channel_);
	names_delayed_waiting=0;

def do_server(nick_, auth_, channel_, msg_):
	print("do_server("+nick_+", "+str(auth_)+", "+channel_+", "+msg_+")\n");
	command=string.upper(string.split(msg_, ' ')[0]);
	netsplit=False;
	if command in ["JOIN", "PART", "QUIT", "KICK"] and auth_>0:
		netsplit=check_netsplit(nick_, channel_, command, msg_);
		if not(netsplit):
			check_sleep_time(nick_, auth_, channel_, command, msg_);
	if command in ["KICK"] and auth_>0:
		kicknick=string.split(msg_, ' ')[2];
		piet.send(channel_, "en waag het niet om weer te komen, jij vuile "+kicknick+"!\n");
	if command in ["437"] and auth_>0:
		piet.send(channel_, "bah, die nick is even niet beschikbaar\n");
	if command in ["353"]:
		check_names(nick_, channel_, msg_);
	if command in ["MODE"] and auth_>0:
		if ((string.find(msg_, ' +o')>=0) or (string.find(msg_, ' -o')>=0)):
			check_names_delayed(channel_);
		else:
			if not(netsplit):
				piet.send(channel_, 'server riep "'+msg_+'", maar dat interesseert echt helemaal niemand\n');
	if command in ["JOIN"]:
		check_names_delayed(channel_);
		

