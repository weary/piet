#!/usr/bin/python

import sys,random,re,time;
sys.path.append(".");
import piet;
import pietlib;

if not("nicks" in vars()):
  nicks={};
if not("topic" in vars()):
  topic=[]

def doe_gemiddelde_offlinetijd(channel_, nick_, tu_):
  print("doe_gemiddelde_offlinetijd("+channel_+", "+nick_+", "+str(tu_)+")\n");
  # CREATE TABLE offline(channel string, nick string, tijd int)

  # CREATE TEMPORARY TABLE t(tijd int);
  # .import weary_offlinetijd.txt t
  # INSERT INTO offline SELECT "#^Ra^Re_mensen", "weary", tijd FROM t;
  # DROP TABLE t

  chan=channel_.replace('"', '""').lower();
  nick=nick_.replace('"', '""').lower();
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
  avg=float(piet.db(query)[1][0]);
  return int(avg);
  
  
def check_sleep_time(nick_, auth_, channel_, command_, msg_):
  print("check_sleep_time("+nick_+", "+str(auth_)+", "+channel_+", "+command_+", "+msg_+")\n");
  # CREATE TABLE logout(
  #    channel string, nick string, tijd int, reason string,
  #    primary key (channel,nick));

  chan=channel_.replace('"', '""').lower();
  nick=nick_.replace('"', '""').lower();
  if (command_ in ["PART", "QUIT", "KICK"]):
    tijd=str(int(time.time()+0.5));
    reason=msg_[5:].replace('"', '""');
    query='REPLACE INTO logout VALUES("'+chan+'", "'+nick+'", '+tijd+', "'+reason+'")';
    piet.db(query);
  elif (command_ in ["JOIN"]):
    try:
      where='WHERE channel="'+chan+'" and nick="'+nick+'"';
      tijd=piet.db('SELECT tijd FROM logout '+where)[1][0];
      piet.db('DELETE FROM logout '+where);
      tu=int(time.time()+0.5)-int(tijd);
      if (tu>0):
        result=pietlib.format_tijdsduur(tu, 2);

        titel=random.choice(("heer", "meester", "prins", "gast", "joker",
          "orgelspeler", "held", "bedwinger", "plaag", "buitenlander", "mastermind",
          "heerser", "samensteller"));
        subtitel=random.choice(("des duisternis", "van het licht", "des ubers",
          "des modders", "des oordeels", "van de knaagdieren", "overste",
          "ongezien", "enzo", "extraordinaire", "(gevallen)",
          "in rust", "ten strijde", "(onverschrokken)", "van iedereen", "van deze wereld",
          "in de dop", "(te jong)"));
        
        reply="ACTION presenteert: %s, %s %s, weer terug na %s" % (nick, titel, subtitel, result)
        try:
          gemiddeld=doe_gemiddelde_offlinetijd(channel_, nick_, tu);
          reply+=", gemiddeld %s nu" % pietlib.format_tijdsduur(gemiddeld, 2);
        except:
          traceback.print_exc();
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
  # CREATE TABLE netsplit(channel string,nick string, servers string, timeout int, PRIMARY KEY(channel,nick));

  NETSPLIT_TIMEOUT=3600; # seconds
  if (command_ in ["QUIT"]):
    if quitmsg_is_split(msg_):
      chan=channel_.replace('"', '""').lower();
      nick=nick_.replace('"', '""').lower();
      servers=msg_[6:].replace('"', '""');
      tijd=str(int(time.time()+0.5)+NETSPLIT_TIMEOUT);
      query='REPLACE INTO netsplit VALUES("'+chan+'", "'+nick+'", "'+servers+'", '+tijd+')';
      piet.db(query);
      return True;
  elif (command_ in ["JOIN"]):
    chan=channel_.replace('"', '""').lower();
    nick=nick_.replace('"', '""').lower();
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
    piet.nick(newnick);
    piet.send(channel_, "wat een prutnaam, dat "+nick_+", ik heet veel liever "+newnick+"\n");
  else:
    try:
      otherauth=piet.db("SELECT name,auth,timezone FROM auth where name=\""+newnick+"\"")[1];
    except:
      otherauth=[newnick, -5, pietlib.LOCALTIMEZONE];

    try:
      auth=piet.db("SELECT name,auth,timezone FROM auth where name=\""+nick_+"\"")[1];
    except:
      auth=[nick_, -5, pietlib.LOCALTIMEZONE];

    print("nickswap: "+repr(auth)+" en "+repr(otherauth)+"\n");
    piet.db("REPLACE INTO auth VALUES(\""+auth[0]+"\", "+str(otherauth[1])+", \""+otherauth[2]+"\")");
    piet.db("REPLACE INTO auth VALUES(\""+otherauth[0]+"\", "+str(auth[1])+", \""+auth[2]+"\")");

    if (auth[1]>otherauth[1]):
      piet.send(channel_, "authenticatie "+str(auth[1])+" nu naar "+newnick+" overgezet, "+\
          nick_+" heeft 't niet meer nodig lijkt me\n")
    elif auth[1] == otherauth[1] and auth[1]>0:
      piet.send(channel_, "authenticatie van "+str(nick_)+" en "+newnick+ " zijn gelijk, niks veranderd\n")
    elif (auth[1]<otherauth[1] and auth[1]>0):
      piet.send(channel_, "authenticatie "+str(auth[1])+" nu naar "+newnick+
					" overgezet, niet nickchangen om hogere auth te krijgen\n")
  
  if nicks.has_key(nick_):
    nicks[newnick]=nicks[nick_];
    del nicks[nick_];
  check_names_delayed(channel_);

def checkmessages(channel_):
  global nicks;
  where="WHERE lower(nick) IN ("+','.join(['"'+x.lower()+'"' for x in nicks])+")";
  msgs=piet.db("SELECT nick,msg FROM notes "+where);
  if (msgs!=None and len(msgs)>=2):
    piet.db("DELETE FROM notes "+where);
    msgs=[n+": "+m for n,m in msgs[1:]];
    piet.send(channel_, '\n'.join(msgs));

def check_names(nick_, channel_, msg_):
  global nicks;
  print("check_names("+nick_+", "+channel_+", "+msg_+")\n");
  msg_nicks=msg_[msg_.find(':')+1:].split(' ');
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
           ','.join(['"'+x+'"' for x in noop])+")";
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

if not(vars().has_key("names_delayed_waiting")):
  names_delayed_waiting=0;

def check_names_delayed(channel_):
  global names_delayed_waiting;
  if (names_delayed_waiting>0):
    return;
  names_delayed_waiting=1;
  time.sleep(5);
  names_delayed_waiting=0;
  piet.names(channel_);

def do_server(nick_, auth_, channel_, msg_):
  global nicks,topic;
  print("do_server("+nick_+", "+str(auth_)+", "+channel_+", "+msg_+")\n");
  command=msg_.split(' ')[0].upper();
  netsplit=False;
  if command in ["JOIN", "PART", "QUIT", "KICK"]:
    if auth_>0:
      print("check_netsplit("+nick_+", "+channel_+", "+command+", "+msg_+"): ");
      netsplit=check_netsplit(nick_, channel_, command, msg_);
      print(repr(netsplit)+"\n");
      if not(netsplit):
        check_sleep_time(nick_, auth_, channel_, command, msg_);
    check_names_delayed(channel_);
  if command in ["PART", "QUIT"]:
    try:
      del nicks[nick_];
    except:
      piet.send(channel_, "voor jullie informatie: het schijnt dat er hier een "+nick_+" was, maar ik heb 'm niet gezien\n");
  if command in ["KICK"] and auth_>0:
    kicknick=msg_.split(' ')[2];
    piet.send(channel_, "en waag het niet om weer te komen, jij vuile "+kicknick+"!\n");
    try:
      del nicks[nick_];
    except:
      piet.send(channel_, "niet dat je er was, maar toch\n");
  if command in ["NICK"]:
    nickchange(nick_, auth_, channel_, msg_[5:]);
  if command in ["437"] and auth_>0:
    piet.send(channel_, "bah, die nick is even niet beschikbaar\n");
  if command in ["353"]:
    check_names(nick_, channel_, msg_);
  if command in ["TOPIC"]:
    nu = time.time()
    newtopic = msg_.split(' ', 1)[1]
    if newtopic.find(':')>=0:
      newtopic = newtopic[newtopic.find(':')+1:]
    if topic:
      delay = nu-topic[-1][0]
      if delay>3*60*60 and topic[-1][1]!=newtopic:
        piet.send(channel_, "\002oude\002 topic van \002%s\002 geleden: %s" % (pietlib.format_tijdsduur(delay,1), topic[-1][1]));
    topic.append((nu, newtopic))
    print "topic lijst bevat nu:", repr(topic)
  if command in ["MODE"] and auth_>0:
    if ((msg_.find(' +o')>=0) or (msg_.find(' -o')>=0)):
      check_names_delayed(channel_);
    else:
      if not(netsplit):
        piet.send(channel_, 'server riep "'+msg_+'", maar dat interesseert echt helemaal niemand\n');
    

