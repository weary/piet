#!/usr/bin/python

import sys,string,random,re,os,time;
import piet;

try:
	nicks;
except:
	nicks={};

localtimezone="Europe/Amsterdam";

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

def nickchange(nick_, auth_, channel_, newnick):
	global nicks;
	print("nickchange("+nick_+", "+str(auth_)+", "+channel_+", "+newnick+"):\n");
	if (newnick[0]==':'): newnick=newnick[1:];
	if (nick_==piet.nick()):
		#piet.nick(newnick);
		piet.send(channel_, "wat een prutnaam, dat "+nick_+", ik heet veel liever "+newnick+"\n");
		return;

	try:
		otherauth=piet.db("SELECT name,auth,timezone FROM auth where name=\""+newnick+"\"")[1];
	except:
		otherauth=[newnick, -5, localtimezone];

	try:
		auth=piet.db("SELECT name,auth,timezone FROM auth where name=\""+nick_+"\"")[1];
	except:
		auth=[nick_, -5, localtimezone];

	print("nickswap: "+repr(auth)+" en "+repr(otherauth)+"\n");
	piet.db("REPLACE INTO auth VALUES(\""+auth[0]+"\", "+str(otherauth[1])+", \""+otherauth[2]+"\")");
	piet.db("REPLACE INTO auth VALUES(\""+otherauth[0]+"\", "+str(auth[1])+", \""+auth[2]+"\")");

	if (auth[1]>otherauth[1]):
		piet.send(channel_, "authenticatie "+str(auth[1])+" nu naar "+newnick+" overgezet, "+\
				nick_+" heeft 't niet meer nodig lijkt me\n");
	elif (auth_<otherauth and auth_>0):
		piet.send("authenticatie "+str(auth_)+" nu naar "+newnick+" overgezet, niet nickchangen om hogere auth te krijgen\n");
	
	nicks[newnick]=nicks[nick_];
	del nicks[nick_];
	check_names_delayed(channel_);

def checkmessages(channel_):
	global nicks;
	where="WHERE nick IN ("+string.join(['"'+x+'"' for x in nicks], ',')+")";
	msgs=piet.db("SELECT nick,msg FROM notes "+where);
	if (msgs!=None and len(msgs)>=2):
		piet.db("DELETE FROM notes "+where);
		msgs=[n+": "+m for n,m in msgs[1:]];
		piet.send(channel_, string.join(msgs, '\n'));

def check_names(nick_, channel_, msg_):
	global nicks;
	print("check_names("+nick_+", "+channel_+", "+msg_+")\n");
	msg_nicks=string.split(msg_[string.find(msg_, ':')+1:], ' ');
	nicks={};
	for x in msg_nicks:
		if (x[0]=='@'):
			nicks[x[1:]]=True;
		else:
			nicks[x]=False;
	pietnick=piet.nick();
	if (nicks[pietnick]):
		noop=[x for (x,o) in nicks.iteritems() if not(o)];
		if (bool(noop)):
			qry="SELECT name FROM auth WHERE auth>=500 AND name IN ("+ \
					 string.join(['"'+x+'"' for x in noop], ',')+")";
			dbres=piet.db(qry);
			if (dbres!=None and len(dbres)>=2):
				print("dbres="+repr(dbres)+"\n");
				res=[x[0] for x in dbres[1:]];
				if (len(res)==1):
					piet.send(channel_, "hup, een apenstaart voor "+res[0]+"\n");
				else:
					piet.send(channel_, "ho, hier moet even wat gefixed worden.\n");
				piet.op(channel_, res);
	else: # piet niet operator
		ops=[x for (x,o) in nicks.iteritems() if o];
		if (bool(ops)):
			myop=random.choice(ops);
			msg=random.choice(["mag ik een @?", "toe, doe eens een @?", \
					"ik wil graag je operatortje zijn, mag ik?", \
					"kijk, ik heb geen @. fix's?", "een @, ah toe?"]);
			piet.send(channel_, myop+": "+msg+"\n");
	checkmessages(channel_);

try:
	names_delayed_waiting;
except:
	names_delayed_waiting=0;

def check_names_delayed(channel_):
	global names_delayed_waiting;
	if (names_delayed_waiting>0):
		return;
	names_delayed_waiting=1;
	time.sleep(5);
	piet.names(channel_);
	names_delayed_waiting=0;

def do_server(nick_, auth_, channel_, msg_):
	global nicks;
	print("do_server("+nick_+", "+str(auth_)+", "+channel_+", "+msg_+")\n");
	command=string.upper(string.split(msg_, ' ')[0]);
	netsplit=False;
	if command in ["JOIN", "PART", "QUIT", "KICK"] and auth_>0:
		netsplit=check_netsplit(nick_, channel_, command, msg_);
		if not(netsplit):
			check_sleep_time(nick_, auth_, channel_, command, msg_);
	if command in ["PART", "QUIT"]:
		del nicks[nick_];
	if command in ["KICK"] and auth_>0:
		kicknick=string.split(msg_, ' ')[2];
		piet.send(channel_, "en waag het niet om weer te komen, jij vuile "+kicknick+"!\n");
		del nicks[nick_];
	if command in ["NICK"]:
		nickchange(nick_, auth_, channel_, msg_[5:]);
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
		

