#!/usr/bin/python
# -*- coding: iso-8859-1 -*-

import sys, string, random, re, os, time, crypt, socket, urllib, types
import traceback, datetime, stat, telnetlib, calendar, math, inspect, shlex
import simplejson

import piet
sys.path.append(".")
import BeautifulSoup
import pietlib
import calc, Distance, pistes, ov9292, kookbalans, bash, gps, ns, vandale

# python 2.5 functions
def all(seq):
  for x in seq:
    if not(x):
      return False;
  return True;

def any(seq):
  for x in seq:
    if x:
      return True;
  return False;

# globals
todofile = "todo.txt";
logfile = "log.txt";

nick = "";#string.strip(sys.stdin.readline());
auth = -5;#int(string.strip(sys.stdin.readline()));
channel = "";#string.strip(sys.stdin.readline());
functions={};
meer_data={};



if not("nicks" in vars()):
  nicks = {};
if not("topic" in vars()):
  topic = []

def db_get(table, keycol, key, valuecol):
  try:
    result=piet.db("SELECT "+valuecol+" FROM "+table+" WHERE "+
        keycol+"=\""+key+"\"");
    return result[1][0];
  except:
    return None;

def db_set(table, key, value):
  try:
    piet.db("REPLACE INTO "+table+" values('"+str(key)+"', '"+str(value)+"')");
    return;
  except:
    piet.db("CREATE TABLE "+table+"(key string primary key, value string)");
    piet.db("REPLACE INTO "+table+" values('"+str(key)+"', '"+str(value)+"')");
    return;

def datum(params):
  tz=pietlib.tijdzone_nick(nick);
  os.environ['TZ']=tz;
  time.tzset();
  dagen = ("maandag", "dinsdag", "woensdag", "donderdag", "vrijdag",
      "zaterdag", "zondag")
  localtime = time.localtime()
  weekday = dagen[localtime.tm_wday % 7]
  result = time.strftime("%d-%m-%Y" , localtime)
  result = "Het is nu %s %s (in de tijdzone %s)" % (weekday, result,
      tz.lower())
  pietlib.timezone_reset();
  return result;

def error_handler(typ, value, tb):
  traceback.print_exc();
  piet.send(channel, "arg! er heeft weer iemand zitten prutsen! wie is't? ik "+
      "moet even "+repr(value.args[0])+" op z'n voorhoofd tatoeëren\n");
  sys.__excepthook__(typ, value, tb); # huh? invalid symbol name. does this work?

sys.excepthook=error_handler;

def parse(param, first, magzeg):
  print "HELP! PIET STUK\n";
  return "";


def leeg(param):
  return "";


def onbekend_commando(param):
  param=string.strip(param);
  groeten=["hoi", "goeiemorgen", "goedemorgen", "mogge", "hallo", "middag"];

  split=string.split(param);
  if len(split)>=2 and any(x in nicks for x in split[1:]):
    return emote(split[0],split[1:]);

  if (len(param)==0):
    return "ok\n"
  elif split[0]=="wanneer":
    return random.choice(["nog lang niet", "voorlopig niet", "echt geen idee", "met sint juttemis"])
  elif param.startswith("hoe is het met "):
    return random.choice(["goed", "slecht", "matig", "het gaat"])
  elif len(split)>2 and split[0]=="is" and split[1]=="het":
    return "dunno"
  elif len(split)>1 and split[0]=="waarom":
    return random.choice(["nergens om", "is vast een goeie reden voor", "gaat je niks aan", "waarom zijn de banananen krom", "ik ga er even voor je over denken, vraag het straks nog maar eens", "geen reden"])
  elif (param[-1]=='?'):
    if (random.random()>=0.475):
      return "ja\n"
    else:
      return "nee\n"
  elif param in groeten:
    return random.choice(groeten)+"\n"
  elif param in ["stfu"]:
    return "jaja, ik zeur\n"
  return random.choice(["goh", "nou", "sja", "och"])+"\n"


def emote(action, remainder):
	if len(action)==0 or len(remainder)==0:
		return "ACTION frot";
	toevoeging=["met tegenzin", "dan maar even", "met een diepe zucht", \
						 "enthousiast", "zonder genade", "alsof z'n leven ervan afhangt",\
						 "nauwelijks", "bijna, maar toch maar niet", "vol overgave"];
	if action=="aai":
		action="aait"
	if action=="gooi":
		action="gooit"
	if action[-1] in "aeoui":
		action=action+action[-1]
	if action[-1]!='t':
		action=action+"t"
	return "ACTION "+action+" "+random.choice(toevoeging)+" "+" ".join(remainder)


def convert(char):
  if (char=="\xb4"):
    return "";
  elif (char=="\xb7"):
    return ".";
  else:
    return char;

def auth_iedereen(params):
  result=[];
  pietnick=piet.nick();
  for i in nicks:
    if i==pietnick: continue;
    c="Europe/Amsterdam"
    try:
      c=piet.db("SELECT timezone FROM auth WHERE name=\""+i+"\"")[1][0];
    except:
      traceback.print_exc();
    result.insert(0, (i, c));
  piet.db("DELETE FROM auth");
  for (n,c) in result:
    a=1000;
    if n==nick: a=1200;
    piet.db("INSERT INTO auth VALUES(\""+n+"\", "+repr(a)+", \""+c+"\")");
  return "iedereen!";

def change_auth(params):
  global nicks;
  localauth=auth;
  newauth=0;
  par=[];
  if (len(params)>0): par=string.split(params, ' ');
  parcount=len(par);
  if (parcount!=0 and parcount!=2 and parcount!=3):
    return "auth [<newauth> <nick> [<password>]]";

  if (parcount==0):
    try:
      pietnick=piet.nick();
      ns=set(nicks)-set([pietnick]);
      try:
        a=piet.db("SELECT name,auth FROM auth ORDER BY name")[1:];
        a=set([(na,au) for (na,au) in a if not(na==pietnick)]);
      except:
        a=set([]);

      anames=set([n for (n,au) in a]);
      
      present=set([(n,au) for (n,au) in a if (n in ns)]);
      away=a-present;
      unknown=ns-anames;

      if (len(present)>0):
        present=pietlib.make_list([n+"("+str(a)+")" for (n,a) in present]);
      else:
        present="niemand";
      if (len(away)>0):
        away=pietlib.make_list([n+"("+str(a)+")" for (n,a) in away]);
      if (len(unknown)>0):
        unknown=pietlib.make_list(unknown);
      else:
        unknown="niemand";

      msg="Van de aanwezigen ken ik "+present+", en ken ik "+unknown+" niet.";
      if (len(away)>0):
        msg=msg+" "+away+" ken ik ook nog, maar die zijn hier niet";
      return msg;
    except:
      traceback.print_exc();
      return "ik heb geen idee, zoek het lekker zelf uit";

  newauth=0; parnick="";
  try:
    newauth=int(par[0]);
    parnick=par[1];
  except:
    try:
      newauth=int(par[1]);
      parnick=par[0];
    except:
      return "anders geef je even een nummer voor de auth die je wilt"
  if (newauth>1500): newauth=1500;
  if (newauth<-1500): newauth=-1500;

  if (parcount==3):
    encrypted=crypt.crypt(par[2], "AB");
    print "AUTH: encrypted ww = \""+encrypted+"\"\n";
    if (encrypted=="ABVBPZGw0mmyg"):
      # user can give authorization as-if his authorisation was 1000
      localauth=max(localauth, 1000);
    else:
      return "achja, leuk geprobeerd, niet goed helaas..\n";

  try:
    dbresult=piet.db("SELECT auth FROM auth WHERE name=\""+parnick+"\"");
    oldauth=int(dbresult[1][0]);
  except:
    oldauth=-5;

  oldauth=int(db_get("auth", "name", parnick, "auth") or -5);
  if (newauth>localauth):
    return "je hebt maar "+str(localauth)+" auth, dus meer mag je niet geven";
  if (localauth<=oldauth and parnick!=nick):
    return "en wie ben jij dan wel, dat je zomaar denkt "+parnick+\
      " authorisatie te kunnen geven?!?";
  if (newauth<=localauth and localauth>=oldauth):
    oldtz=db_get("auth", "name", parnick, "timezone");
    if (oldtz):
      piet.db("REPLACE INTO auth(name,auth,timezone) VALUES(\""+
          parnick+"\","+str(newauth)+",\""+oldtz+"\")");
    else:
      piet.db("REPLACE INTO auth(name,auth) VALUES(\""+parnick+"\","+
          str(newauth)+")");
    # check_names(nick_, channel_, msg_), would be nice, strange library
    # dependancy though
    return "ok, "+parnick+" heeft nu authenticatieniveau "+str(newauth)+"\n";
  return "bogus"; # never reached, i think


if not(vars().has_key("boottime")):
  boottime=time.time();

def hex2dec(params):
  if params[:2]=="0x" or params[-1]=='h':
    if params[-1]=='h': params=params[:-1]
    if params[:2]=='0x': params=params[2:]
    try:
      val=int(params, 16)
    except:
      traceback.print_exc()
      return "doe nou niet alsof dat hexadecimaal is.. dat is't niet"
    result="0x"+params+" wordt door sommigen aangeduid als "+str(val)
    if (val>=2**7 and val<=2**8):
      result+=", en soms ook als -"+str(2**8-val)
    elif (val>=2**15 and val<=2**16):
      result+=", en soms ook als -"+str(2**16-val)
    elif (val>=2**31 and val<=2**32):
      result+=", en soms ook als -"+str(2**32-val)
    elif (val>=2**63 and val<=2**64):
      result+=", en soms ook als -"+str(2**64-val)
    return result
  try:
    print "converting \""+params+"\""
    val=int(params)
  except:
    traceback.print_exc()
    return "ACTION stuurt een grote boze heks op je af"
  hex2 = lambda x: hex(x).replace('L','')
  if (val>=0):
    result = str(val)+" is ook wel "+hex2(val)
    if val>=2**7 and val <2**8:
      result += ", maar misschien was er wel "+str(val-2**8)+" bedoeld"
    elif val>=2**15 and val <2**16:
      result += ", maar misschien was er wel "+str(val-2**16)+" bedoeld"
    elif val>=2**31 and val <2**32:
      result += ", maar misschien was er wel "+str(val-2**32)+" bedoeld"
    elif val>=2**63 and val <2**64:
      result += ", maar misschien was er wel "+str(val-2**64)+" bedoeld"
    return result
  if (val>=-(2**7)):
    return str(val)+" is dus "+hex2(2**8+val)
  elif (val>=-(2**15)):
    return str(val)+" is dus "+hex2(2**16+val)
  elif (val>=-(2**31)):
    return str(val)+" is dus "+hex2(2**32+val)
  elif (val>=-(2**63)):
    return str(val)+" is dus "+hex2(2**64+val)
  else:
    return str(val)+" is wel heel klein, "+hex2(val)


def hex_no_l(v):
	r = hex(v)
	if r[-1] == 'L':
		return r[:-1]
	return r

def hton(params):
	p = params.split()

	bytes = 0
	if len(p) >= 2:
		if p[0].lower() == 's' or p[0] == '16':
			bytes = 2
			del p[0]
		elif p[0].lower() == 'l' or p[0] == '32':
			bytes = 4
			del p[0]
		elif p[0] == '64':
			bytes = 8
			del p[0]

	value = ' '.join(p)
	if not p:
		return "ACTION zet het niets maar eens in omgekeerde volgorde"

	try:
		if value[:2] == "0x":
			value = int(value[2:], 16)
		elif value[-1].lower() == "h":
			value = int(value[:-1], 16)
		else:
			try:
				value = int(value)
			except:
				value = int(value, 16)
	except:
		try:
			value = int(parse(value, False, True))
		except:
			traceback.print_exc()
			return "tja, '%s' is omgekeerd '%s'" % (
					params, ''.join([params[i] for i in range(len(params)-1,-1,-1)]))

	if not bytes:
		if value>=(1<<32):
			bytes = 8
		elif value>=(1<<16):
			bytes = 4
		else:
			bytes = 2

	rev = 0
	work = value
	for i in range(0, bytes):
		rev = (rev << 8) + (work & 0xFF)
		work = work >> 8

	return "de waarde %d (%s) zou door grote indianen gezien worden als %d (%s)" % (
			value, hex_no_l(value), rev, hex_no_l(rev))



def weekend(params):
  tz=pietlib.tijdzone_nick(nick);
  os.environ['TZ']=tz;
  time.tzset();
  tijd=time.gmtime();
  wday=(tijd.tm_wday + (tijd.tm_wday==4 and tijd.tm_hour>=17) ) % 7;
  l={
  0: ["ja, maandag, 't weekend weer overleefd", "grr, een maandag"],
  1: ["pff, dat duurt nog lang, pas dinsdag",
      "dinsdag, alweer 1 dag gehad, nog veel te gaan"],
  2: ["woensdag, op de helft", "woensdag, 2 down, 3 to go"],
  3: ["donderdag, komt in de buurt",
      "pff, vandaag nog, en die hele vrijdag nog"],
  4: ["vrijdag! bijna!", "vandaag nog ff doorkomen en we zijn er!"],
  5: ["jaaah! weekend!"],
  6: ["jaaah! de hele dag nog weekend!"]
  }[wday];
  pietlib.timezone_reset();
  return random.choice(l);

def uptime(params):
  ut=time.time()-boottime;
  minutes,seconds=int(ut/60),int(ut%60);
  hours,minutes=int(minutes/60),int(minutes%60);
  days,hours=int(hours/24),int(hours%24);
  if (days>100):
    return "ben oud... " + pietlib.format_tijdsduur(ut)
  elif (days>31):
    return "ben met " + pietlib.format_tijdsduur(ut) + " toch een goede irc verslaafde"
  elif (days>1):
    return "woei! alweer " + pietlib.format_tijdsduur(ut)
  elif (days>0):
    return "toch alweer " + pietlib.format_tijdsduur(ut)
  elif (hours>1):
    return "alweer " + pietlib.format_tijdsduur(ut)
  elif (hours>0):
    return "nog maar " + pietlib.format_tijdsduur(ut)
  else:
    return pietlib.format_tijdsduur(ut)


def kies(params):
	if not params.strip():
		return "ACTION kiest voor zichzelf"
	try:
		choices = shlex.split(params)
	except Exception, e:
		return "sja, wat denk je er zelf van, wat zou JIJ kiezen? ik ben van mening dat " + str(e)
	choice = random.choice(choices)
	if not choice:
		return "ACTION maakt een lege keuze"
	choice = parse(choice, False, True)
	return choice.strip()

def rijm(woord):
  try:
    inp=pietlib.get_url("http://www.rijmwoorden.nl/rijm.pl?woord="+
        woord.strip());
  except:
    return "ik kan niet rijmen zonder de website, "+\
      "dus je zult 't zelf moeten doen";
  soup=BeautifulSoup.BeautifulSoup(inp);
  woorden=[str(x.string) for x in soup.table("td") if x.string];
  if (len(woorden)==0):
    return "daar rijmt echt helemaal niks op";
  return "oh, dat is makkelijk: "+", ".join(woorden);

def urban(params):
  # darn thing has a SOAP interface :(
  header= \
    "POST /soap HTTP/1.1\r\n" \
    "Host: api.urbandictionary.com\r\n" \
    "Content-Type: text/xml\r\n" \
    "Content-Length: ";
  body= \
  '<?xml version="1.0" encoding="UTF-8"?>' \
  '<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">' \
     '<soapenv:Body>' \
        '<ns1:lookup soapenv:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/" xmlns:ns1="urn:UrbanSearch">' \
          '<key xsi:type="xsd:string">ab4756bc8aaad15f2b5a54fdf398f112</key>' \
          '<term xsi:type="xsd:string">%SEARCHWORD%</term>' \
        '</ns1:lookup>' \
     '</soapenv:Body>' \
  '</soapenv:Envelope>';

  a=string.replace(body, "%SEARCHWORD%", params);
  s=socket.socket(socket.AF_INET, socket.SOCK_STREAM);
  s.connect(("api.urbandictionary.com", 80));
  fs=s.makefile();
  s.sendall(header+str(len(a))+"\r\n\r\n"+a);
  x='<?xml'+string.split(fs.read(), '<?xml')[1]; #read only the part after <?xml

  import libxml2
  import libxslt

  sheettext=\
  "<xsl:stylesheet version='1.0' xmlns:xsl='http://www.w3.org/1999/XSL/Transform'>"\
    "<xsl:output method='text'/>"\
    "<xsl:template match='/'>"\
      "<xsl:for-each select='/*/*/*/return/item'>"\
        "<xsl:value-of select='definition'/>"\
        "<xsl:for-each select='example'> (bijvoorbeeld: \"<xsl:value-of select='.'/>\")</xsl:for-each>"\
        "LINEBREAKHIER"\
      "</xsl:for-each>"\
    "</xsl:template>"\
  "</xsl:stylesheet>";

  styledoc = libxml2.parseDoc(sheettext);
  style = libxslt.parseStylesheetDoc(styledoc);
  doc = libxml2.parseDoc(x);
  result = style.applyStylesheet(doc, None);
  try: lines=style.saveResultToString(result);
  except: lines="*daar* weet ik niks van, probeer vandale eens ofzo";
  style.freeStylesheet();
  doc.freeDoc();
  result.freeDoc();
  lines=string.replace(lines, "\n", " ");
  lines=string.replace(lines, "\r", "");
  lines=string.replace(lines, "LINEBREAKHIER", ".\n");
  return lines;

def makeenterfromnull(inp):
  if inp=="":
    return "\n";
  else:
    return inp;

def SydWeer(params):
  cmd="lynx -dump http://www.smh.com.au/weather/sydney.html";
  inp,outp,stderr = os.popen3(cmd);
  result=outp.read();
  inp.close();
  outp.close();
  stderr.close();
  i=string.find(result,"tate Sum")+22;
  j=string.find(result,"___",i);
  result=string.split(string.strip(result[i:j]),'\n');
  fresult="";
  for s in result:
    fresult+=string.strip(s)+" ";
  return fresult;

def nlweer(woord):
	all = pietlib.get_url('http://api.twitter.com/1/statuses/user_timeline/buienradarnl.xml')
	text = re.findall('<text>(.*?)</text>', all)
	for i in text:
		if i[:1]!='@':
			return i
	return "geen idee, kijk eens naar buiten ofzo.."

def itaweer(woord):
  if (woord=="it"):
    cmd = "wget -O - \"http://www.televideo.rai.it/televideo/pub/solotesto.jsp?regione=&pagina=704&sottopagina=01\" 2>/dev/null | grep -A 2 PISA | perl -ni -e 'trim; $_ =~ s/\s+/ /g; print \"Oggi: $_\\n\";';wget -O - \"http://www.televideo.rai.it/televideo/pub/solotesto.jsp?regione=&pagina=705&sottopagina=01\" 2>/dev/null | grep -A 2 PISA | perl -ni -e 'trim; $_ =~ s/\s+/ /g; print \"Domani: $_\\n\";'"
  else:
    cmd = "wget -O - \"http://www.televideo.rai.it/televideo/pub/solotesto.jsp?regione=TOSCANA&pagina=313&sottopagina=01\" 2>/dev/null | grep -i "+woord+" | perl -ni -e '$_ =~ s/\s+/ /g;($dummy,$loc,$min,$max) = split / /, $_ ; print \"$loc: min=$min max=$max\";'";

  inp,outp,stderr = os.popen3(cmd);
  result=outp.read();
  inp.close();
  outp.close();
  stderr.close();
  return string.strip(result); 

def weer(woord):
  woord=string.lower(woord);
  if (woord[:3]=="syd"):
    return SydWeer(woord);
  elif (woord=="nl") or woord=="":
    return nlweer("");
  elif (nick[:6]=="semyon"):
    return SydWeer("");
  elif (woord=="it" or woord=="pisa" or woord=="lucca"):
    return itaweer(woord);
  return "'%s' ken ik niet hoor, hier is het nederlandse weer:\n%s" %\
    (woord,nlweer(""));

if not(vars().has_key("zeghisttijd")):
  zeghisttijd=0;
  zeghistnicks=[];
assert(vars().has_key("zeghisttijd") and vars().has_key("zeghistnicks"));

def zeg(params):
  global nicks,zeghisttijd,zeghistnicks;
  tegen="";
  kanaal=channel;
  split=string.split(params, " ");
  if len(split)>=3 and split[0]=="tegen":
    tegen=split[1];
    split=split[2:];
  if len(split)>=3 and split[-2]=="tegen":
    tegen=split[-1];
    split=split[:-2];
  if len(split)>=3 and split[0]=="op":
    kanaal=split[1];
    split=split[2:];
  if len(split)>=3 and split[-2]=="op":
    kanaal=split[-1];
    split=split[:-2];
  
  if kanaal==channel and tegen=="":
    return params;
  if kanaal!=channel and tegen!="":
    return "tegen en op tegelijk? dit wordt te ingewikkeld voor mij hoor.."
  
  txt=string.join(split, " ");
    
  if tegen!="":
    if (nicks.has_key(tegen)):
      return tegen+", ehm, "+txt;
    elif (auth>100):
      txt=txt.replace("'", "''");
      piet.db("INSERT INTO notes VALUES('"+tegen+"','"+txt+"')");
      return "ik zie helemaal geen "+tegen+". misschien later";
    else:
      return "doe het lekker zelf ofzo";
  
  piet.send(kanaal, txt);
  now=time.time();
  zeghisttijd=now;
  zeghistnicks.append(nick);
  time.sleep(3*60);
  if zeghisttijd==now:
    n=unique(zeghistnicks);
    zeghistnicks=[];
    piet.send(kanaal, "zo, dat heb ik even goed gezegd, niet dan "+
        pietlib.make_list(n)+"?");
  return "";

def rot_nr(cmd):
  if not (cmd[:1]>"0" and cmd[:1] <= "9"):
    return onbekend_commando("rot"+cmd)
  n,y=string.split(cmd, " ", 1);
  n=int(n)%26;
  y=string.strip(parse(y, False, True));
  def rot_char(x):
    if not(x.isalpha()): return x;
    p=ord(x.lower())-ord('a');
    assert(p>=0 and p<26);
    p2=(p+n)%26;
    return chr(ord(x)-p+p2);
  return string.join(map(rot_char,y), '');

# make sure every entry occurs only once
def unique(l):
  try:
    u = {}
    for x in l:
      u[x.lower()] = x
    return u.values()
  except:
    traceback.print_exc();

def conf(s):
  return s.encode('latin1', 'replace');

def afk(params):
  params=params.strip();
  if not(params):
    return "dacht 't niet";
  params=params.split(' ', 1);
  woord=params.pop(0);
  result1=afk_source1(woord);
  result2=afk_source2(woord);
  result3=afk_source3(woord);

  result=result1;
  rest=[];

  if (len(result)>8):
    rest=result2+result3;
  else:
    result=unique(result1+result2);
    if (len(result)>8):
      rest=result3;
    else:
      result=unique(result1+result2+result3);

  s="";
  if len(result)==0:
    s="niks gevonden!\n";
  else:
    s=pietlib.make_list(result);
    if len(rest)>0:
      s+="\nik weet nog %d verklaringen voor \"%s\" maar die vertel ik niet." %\
        (len(rest), woord);
  
  return s;

def afk_source2(woord):
  try:
    a=pietlib.get_url_soup(
        "http://www.afkorting.net/cgi-local/s.pl?pg=a&s=%s" % woord);
    r=a.table.findAll("tr", recursive=False);
    r=[i.findAll("td") for i in r];
    r=[conf(i[1].contents[0]) for i in r if len(i)>=2];
    return r;
  except:
    traceback.print_exc();
    piet.send(channel,
        "helaas, afkortingen.net wilde me niet te woord staan\n");
  return [];

# input: searchword
# output: list of possible meanings
def afk_source3(woord):
  try:
    a=pietlib.get_url_soup(
        "http://acronyms.thefreedictionary.com/"+woord, "bla/bla");
    r=a("table", {'class': 'AcrFinder'})[0]('tr');
    r=[i("td", recursive=False) for i in r];
    r=[conf(i[1].contents[0]) for i in r if len(i)>=2];
    return r;
  except:
    traceback.print_exc();
    piet.send(channel, "helaas, thefreedictionary is veel te ver weg\n");
  return [];
    

def afk_source1(woord):
  try:
    woord=woord.lower();
    wordmap=open("afk.txt").read().split("\n");
    wordmap=[i.split('#', 1) for i in wordmap];
    return [i[1] for i in wordmap if len(i)>=2 and i[0].lower()==woord];
  except:
    traceback.print_exc();
    piet.send(channel,
        "helaas, de afkortingen die ik uit m'n hoofd ken zijn zoek\n");
  return [];

def changelog(params):
  command=\
    "darcs cha --last=5 | "+\
    "sed -e '/^$/d;N;s/\\n//g;s/<[a-zA-Z]\\+@[a-zA-Z\\.]\\+>//;s/[\\t\\ ]\\+/ /g'";
  inp = os.popen(command);
  result=inp.read();
  inp.close();
  return "echt veel is er niet veranderd...\n"+result;

def spell_int(woorden, lang):
  outp, inp = os.popen2("aspell -a --lang="+lang);
  outp.write(woorden);
  outp.close();
  result=string.split(inp.read(), '\n');
  result=[re.sub("& (\w+) \d+ \d+:", "\\1: ", i)
      for i in result[1:]
      if (i!="*") and (i!="")];
  if len(result)==0:
    return "dat is goed gespeld\n";
  else:
    return string.join(result, '\n')+"\n";

def spell_nl(woorden):
  woorden = string.strip(parse(woorden, False, True));
  return spell_int(woorden, "nl");

def spell_de(woorden):
  woorden = string.strip(parse(woorden, False, True));
  return spell_int(woorden, "de");
  
def spell_en(woorden):
  woorden = string.strip(parse(woorden, False, True));
  return spell_int(woorden, "en_GB-only");


def random_sentence(params):
  url="http://watchout4snakes.com/creativitytools/RandomSentence/RandomSentence.aspx";
  try:
    s=pietlib.get_url_soup(url);
    l=s.findAll("span", {"class":"randomSentence"})[0].contents[0];
    return l.encode();
  except:
    traceback.print_exc();
    return "'t is stuk, nu geen zin";

def command_help(param):
	param = param.strip()
	if not param:
		categories = dict([ (tup[0], 0) for (_, tup) in functions.iteritems() ]).keys()
		for cat in categories:
			r = [ fun for (fun, tup) in functions.iteritems() if tup[0] == cat and tup[3] ]
			if r:
				r.sort()
				cmds = len(r)
				r = ', '.join(r)
				piet.send(channel, "%s(%d commands): %s\n" % (cat, cmds, r))
		return ""
	else:
		if param not in functions:
			return "daarmee kan ik je niet helpen. eigenlijk weet ik niet eens wat het is.."
		h = functions[param][3]
		if not h:
			return "tja, goeie vraag wat dat doet. ik weet 't niet"
		else:
			return h

def alias(params):
  r=[b for b in functions if (functions[b][3]=="") and (functions[b][1]<=auth)];
  r.sort();
  return string.join(r, ', ')+"\n";

def spreuk(params):
  inf = open("ol.txt");
  lines = string.split(inf.read(), '\n');
  inf.close();
  return random.choice(lines)+"\n";

def ping(woord):
  a=string.split(woord, ' ');
  if len(a)!=1 or len(a[0])==0 or a[0]=='?':
    return nick+": pong\n";
  else:
    inp = os.popen("ping -q -c 10 "+a[0]+" | tail -n 2");
    result=inp.read();
    return result+"\n";

def zoek(param):
  if (param=="vrouw"):
    return zoekvrouw(param);
  return 'alleen "zoek vrouw" werkt'

def zoekvrouw(params):
  cmd="lynx --width=1000 --dump 'http://www.onehello.nl/search/quickSearchAction.jsp?myGender=134&gender=135&ageFrom=18&ageTo=30&loctype=country_division&findDivisionsAndReload=false&countryvalue=146&findCitiesAndReload=false&divisionvalue=652&LastActive=&LastJoined=&Smoking=&HaveChildren=&format=200&template=SearchQuickSearch&statsJS=JS&statsWinWidth=1272&statsWinHeight=874&k=2764037968126736068&s=6575419&l=nl&t=GUEST' | "
  cmd+="sed -n '/Resultaten 1 tot en met/,/^[[:blank:]]*$/p' | ";
  cmd+="sed -n '/naam/{s/^.*]//;h};/Leeftijd/{s/.*: /, /;H};/Lokregel/{s/.*: /: /;H;g;s/\\n//g;p}'";
  inp = os.popen(cmd);
  vrouwen = string.split(inp.read(), '\n');
  inp.close();
  result = random.choice(vrouwen) + '\n';
  result+= random.choice(vrouwen) + '\n';
  result+= random.choice(vrouwen) + '\n';
  return result;

def vertaal(regel):
	aliassen = dict((
			("dutch", "nl"),("nederlands", "nl"),
			("english", "en"),("engels", "en"),
			("spanish", "es"),("spaans", "es"),
			("german", "de"),("duits", "de"),
			("french", "fr"),("frans", "fr"),
			("arabic", "ar"),("arabic", "ar")))
	talen = 'auto ar bg ca cs da de el en es fi fr hi hr id it iw ja ko lt lv nl no pl pt ro ru sk sl sr sv tl uk vi zh-CN zh-TW'.split(' ')
	talenre = '|'.join(aliassen.keys()+talen)
	reresult = re.match('\s*(?:(%s)\s+)?(?:(%s)\s+)?(.*)' % (talenre,talenre), regel)
	if not reresult:
		return "beetje onwaarschijnlijk dat dit gebeurd, maar ik snap je vraag niet"

	(taal1,taal2,regel) = reresult.groups()
	if taal1 and taal1 in aliassen:
		taal1 = aliassen[taal1]
	if taal2 and taal2 in aliassen:
		taal2 = aliassen[taal2]

	if taal1 and taal2:
		bron = taal1
		doel = taal2
	elif taal1 or taal2:
		bron = "auto"
		doel = taal1 or taal2
	else:
		bron = "auto"
		doel = "nl"

	regel = regel.strip()
	if not regel:
		return "um, ik wil best vertalen, maar je hebt niks gegeven om te vertalen"
	regel2 = str(parse(regel, False, True))
	if regel2:
		regel = regel2
	
	form = { 'client':'t', 'text':regel, 'sl':bron, 'tl':doel }
	url = """http://translate.google.com/translate_a/t?""" + urllib.urlencode(form)
	result = pietlib.get_url(url, agent="Mozilla/5.0").strip()
	if not result:
		return "ik heb helemaal niks teruggekregen, sorry"
	result = simplejson.loads(result.replace(',,',',null,')) # replace because simplejson does not accept [[],,[]]

	bron = result[-1]
	
	out = []
	out.append(result[0][0][0])
	if result[0][0][2]:
		out.append(result[0][0][2])
	seen = set()
	if result[1]:
		for d in result[1]:
			pos = d[0]
			pos = {'noun':'znw','verb':'werkwoord','adjective':'bijv.nw'}.get(pos,pos)
			out.append('als %s: %s' % (pos, pietlib.make_list(d[1], sep="of")))
			for t in d[1]:
				seen.add(t)
	if 'sentences' in result:
		sentence = ''
		for d in result['sentences']:
			if d['trans'] not in seen:
				sentence = sentence + d['trans']
		if sentence:
			out.append('in een zin: %s' % sentence)
	return "%s->%s, %s" % (bron, doel, pietlib.make_list(out))

def dvorak2qwerty(params):
  params = string.strip(parse(params, False, True));
  t=string.maketrans(
      "anihdyujgcvpmlsrxo;kf.,bt/weqANIHDYUJGCVPMLSRXO:KF><BT?WEQ",
      "abcdefghijklmnopqrstuvwxyz,.'ABCDEFGHIJKLMNOPQRSTUVWXYZ<>\"");
  return params.translate(t);

def qwerty2dvorak(params):
  params = string.strip(parse(params, False, True));
  t=string.maketrans(
      """axje.uidchtnmbrl'poygk,qf;wv-AXJE>UIDCHTNMBRL"POYGK<QF:WV_ """,
      """abcdefghijklmnopqrstuvwxyz,.'ABCDEFGHIJKLMNOPQRSTUVWXYZ<>" """);
  return params.translate(t);

def reverse(params):
  params = string.strip(parse(params, False, True));
  return params[-1::-1]

def last(params):
  params = string.strip(params)
  if params[0] == '-':
    params = params[1:]
  try:
    line=int(params);
  except:
    return "alsof jouw mening er wat toe doet" # 'dat' command misused
  inp = os.popen("tail -n "+str(line)+" log.txt | head -n 1");
  result=inp.read();
  return(result);

def leet(params):
  params = string.strip(parse(params, False, True));
  t=string.maketrans("eilatbosgEILATBOSG", "311478059311478059");
  return params.translate(t);
 
def unleet(params):
  params = string.strip(parse(params, False, True));
  t=string.maketrans("311478059", "eilatbosg");
  return params.translate(t);

def todo(params):
  if (params==""):
    inf = open(todofile);
    lines = [a for a in string.split(inf.read(), '\n') if a!=""];
    inf.close();
    if (len(lines)>0):
      for i in range(0, len(lines)):
        lines[i]=str(i)+". "+lines[i];
      return string.join(lines, '\n');
    else:
      return "helemaal niks meer te doen!";
  else:
    inf = open(todofile, "a+");
    inf.write(params+"\n");
    inf.close();
    return "misschien, misschien niet";

def commando_url(params):
  #cmd="sed -n '/http\|www/{s/.*\(http\|www\)/\\1/;T;s/[[:blank:]].*//;p}' log.txt"
  #inp = os.popen(cmd);
  #result = string.split(inp.read(), '\n');
  #inp.close();
  #result = random.choice(result);
  #return result;
  html = pietlib.get_url("http://del.icio.us")

  urls = re.findall(
      '<h4><a href="([^"]*)" rel="nofollow"><img [^>]*>([^<]*)</a>', 
      html, re.MULTILINE | re.IGNORECASE)
  url = random.choice(urls)
  return "%s: %s" % (url[1].strip(), url[0])


def simon(params):
  cmd="w -h simon"
  if os.popen(cmd).read():
    return "ja, een simon"
  else:
    return "nee, nog niet";

def galgje(regel):
  a=string.split(regel, ' ');
  if (len(a)<0):
    return "doe eens galgje start ofzo\n";
  else:
    i1 = string.lower(string.strip(a[0]));
    if (i1 == "start"):
      gf = open("list.txt");
      lines = [a for a in string.split(gf.read(), '\n') if a!=""];
      gf.close();
      index = random.randint(0,len(lines)-1);
      word = lines[index];
      blind = string.join(['-' for a in word]);
      towrite = blind+"\n"+str(index)+"\n7\n \n";
      outf = open("galgjetemp"+channel+".txt","w");
      outf.write(towrite);
      outf.close();
      print "ik heb een nieuw woord bedacht, ga maar raden";
      return blind+" 7";
    elif (i1 == "raad"):
      if (len(a)<2):
        return "je moet een letter raden\n";
      else:
        tempf = open("galgjetemp"+channel+".txt");
        lines = [i for i in string.split(tempf.read(), '\n') if i!=""];
        blind=lines[0];
        index=lines[1];
        times=int(lines[2]);
        gehad=lines[3];
        tempf.close();
        gf = open("list.txt");
        lines = [i for i in string.split(gf.read(), '\n') if i!=""];
        gf.close();
        word=string.lower(lines[int(index)]);
        j=-2;
        nblind = "";
        for i in word:
          j=j+2;
          if (i==a[1]):
            nblind = nblind + i + " ";
          else:
            nblind = nblind + blind[j]+" ";
        if (nblind == blind):
          times=times-1;
          if (gehad == " "):
            gehad = a[1];
          else:
            gehad = gehad + ", " + a[1];
        if (string.find(nblind,"-")==-1):
          return nick+": heel goed. Het was idd "+word;
        if (times==0):
          return "dood, het was: "+word;
        towrite = nblind+"\n"+str(index)+"\n"+str(times)+"\n"+gehad+"\n"
        outf = open("galgjetemp"+channel+".txt","w");
        outf.write(towrite);
        outf.close();
        return nblind+" "+str(times)+" "+gehad;
    else:
      return "doe eens galgje start ofzo\n";
  return "Galgje: Error: Huh? Ik ben opeens aan het einde van mijn procedure"; 

def citaat(params):
  inf = open(logfile);
  lines = string.split(inf.read(), '\n');
  inf.close();
  result=random.choice(lines);
  return(result);

def nmblookup(regel):
  host=string.split(regel, ' ')[0];
  inp = os.popen("nmblookup "+host);
  temp = string.split(inp.read(), '\n');
  if (len(temp)!=3):
    return("arg! help! nmblookup doet raar!\n");
  else:
    lines = string.split(temp[1], ' ');
    if (lines[1]==host+"<00>"):
      result=host+" is vandaag te vinden op "+lines[0]+"\n";
    elif (lines[1]=="failed"):
      inp = os.popen("nmblookup -U 130.89.1.108 -R "+host);
      temp = string.split(inp.read(), '\n');
      if (len(temp)!=3):
        return("arg! help! nmblookup doet raar!\n");
      else:
        lines = string.split(temp[1], ' ');
      if (lines[1]==host+"<00>"):
        result=host+" is vandaag te vinden op "+lines[0]+"\n";
      elif (lines[1]=="failed"):
        result="ik denk dat "+host+" uitstaat, kan 'm niet vinden\n";
    else:
      result="oei, iets mis met nmblookup, ik kreeg \"%s\"\n" %\
              string.join(lines, ' ');
    return(result);

def wat_is(regel):
  regel = regel.strip();
  if regel[-1]=='?':
    regel = regel[:-1].strip();
  ln = regel+" is "
  ww = "is"
  cmd = 'grep -i "%s" log.txt' % ln;
  inp = os.popen(cmd);
  result = inp.read().split('\n');
  if len(result)==0 or (len(result)==1 and len(result[0])==0):
    ln = regel+" zijn "
    ww = "zijn"
    cmd = 'grep -i "%s" log.txt' % ln
    inp = os.popen(cmd)
    result = inp.read().split('\n')
    if len(result)==0 or (len(result)==1 and len(result[0])==0):
      return "%s is helemaal niks, eigenlijk" % regel
  result = random.choice(result);
  pos = result.find(ln);
  if pos>=0:
    result = result[pos+len(ln):];
  pos = result.find('.');
  if pos>0:
    result = result[:pos];
  if len(result) != 0:
    return "volgens mij %s %s %s" % (ww, regel, result);
  return "wat is wat ook weer.."


def context(regel):
  cmd="grep -B2 -A2 \""+regel+"\" log.txt";
  inp = os.popen(cmd);
  result=inp.read();
  result=string.split(result, "\n--\n");
  result.reverse();
  result=string.join(result, "\n--\n");
  return(result);

def watis(regel):
  cmd="dict -P - \""+regel+"\"";
  inp = os.popen(cmd);
  result=inp.read();
  return(result);

def anagram(regel):
  params=string.split(regel, ' ');
  if (len(params)<1) or (len(params[0])==0):
    return "_niks_ is al een anagram van zichzelf\n";
  else:
    woord=string.lower(string.strip(string.join(params,"")));
    if (string.lower(string.strip(params[0])) != "en"):
      c = "wget -O - -q";
      c = c+" \"http://www.ssynth.co.uk/~gay/cgi-bin/nph-an?line=";
      c = c+woord;
      c = c+"&words=1&dict=dutch&doai=on\"";
      outp = os.popen(c);
      result = outp.read();
      i1 = string.rfind(result,"<pre>");
      i2 = string.rfind(result,"</pre>");
      result=result[i1+5:i2];
      result=string.split(result, '\n');
      if (len(result)>1):
        index = random.randint(0,len(result)-2);
        return result[index];
      c = "wget -O - -q";
      c = c+" \"http://www.ssynth.co.uk/~gay/cgi-bin/nph-an?line=";
      c = c+woord;
      c = c+"&words=2&dict=dutch&doai=on\"";
      outp = os.popen(c);
      result = outp.read();
      i1 = string.rfind(result,"<pre>");
      i2 = string.rfind(result,"</pre>");
      result=result[i1+5:i2];
      result=string.split(result, '\n');
      if (len(result)>1):
        index = random.randint(0,len(result)-2);
        return result[index];
    else:
      params=params[1:];
      woord=string.lower(string.strip(string.join(params,"")));
    c = "wget -O - -q";
    c = c+" \"http://www.ssynth.co.uk/~gay/cgi-bin/nph-an?line=";
    c = c+woord;
    c = c+"&words=1&dict=antworthp&doai=on\"";
    outp = os.popen(c);
    result = outp.read();
    i1 = string.rfind(result,"<pre>");
    i2 = string.rfind(result,"</pre>");
    result=result[i1+5:i2];
    result=string.split(result, '\n');
    if (len(result)>1):
      index = random.randint(0,len(result)-2);
      return result[index];
    c = "wget -O - -q";
    c = c+" \"http://www.ssynth.co.uk/~gay/cgi-bin/nph-an?line=";
    c = c+woord;
    c = c+"&words=2&dict=antworthp&doai=on\"";
    outp = os.popen(c);
    result = outp.read();
    i1 = string.rfind(result,"<pre>");
    i2 = string.rfind(result,"</pre>");
    result=result[i1+5:i2];
    result=string.split(result, '\n');
    if (len(result)>1):
      index = random.randint(0,len(result)-2);
      return result[index];
    return "sorry ik kan niks bedenken";

def discw(regel):
  params=string.split(regel, ' ');
  if (len(params)<1) or (len(params[0])==0):
    return "gebruik dw <speler> met <speler> een spelersnaam op dw\n";
  else:
    tn = telnetlib.Telnet('discworld.imaginary.com', 4242);
    tn.read_until("Your choice:");
    tn.write("f\n");
    tn.read_until("to finger?");
    tn.write(params[0]+"\n");
    result=tn.read_until("Press enter to continue");
    i=string.find(result,"On since");
    if (i>0):
      j=string.find(result,".",i);
      j=string.find(result,".",j+1);
      return result[i:j];
    i=string.find(result,"Last logged o");
    j=string.find(result,".",i);    
    return result[i:j];
   
def discwho(params):
  matchtext1="Press enter to continue";
  matchtext2="Here is a list of the people currently playing Discworld:";

  tn = telnetlib.Telnet('discworld.imaginary.com', 4242);
  tn.write("u\nq\n");
  outp=tn.read_until(matchtext1);
  tn.close();
  outp=outp[outp.find(matchtext2)+len(matchtext2):outp.find(matchtext1)];
  outp=outp.replace("\r", "").replace("\n", "").lower();
  outp=set(re.split(",[ \t]*", outp));
  result=outp.intersection(("irk", "taido", "szwarts", "quences", "weary"));
  if not(result):
    return "niemand!";
  if len(result)==1:
    return "op discworld is op dit moment: "+', '.join(result);
  return "op discworld zijn op dit moment: "+', '.join(result);

def geordi(params):
  A=random.choice((
        "perform a level E diagnostic on", "run a level E diagnostic on",
        "reroute the B C D to", "redirect the B C D to", "divert the B C D to",
        "bypass", "amplify", "modify", "polarize", "reconfigure", "extend",
        "rebuild", "vary", "analyze", "adjust", "recalibrate"));
  A="we need to "+A+" the B C D!";
  while A.find("B")>=0:
    B=random.choice((
          "field", "tachyon", "baryon", "lepton", "e-m", "phase", "pulse",
          "sub-space", "spectral", "antimatter", "plasma", "bandwidth",
          "particle"));
    A=A.replace("B", B, 1);
  while A.find("C")>=0:
    C=random.choice(("dispersion", "induction", "frequency", "resonance"));
    A=A.replace("C", C, 1);
  while A.find("D")>=0:
    D=random.choice((
          "conduit", "discriminator", "modulator", "transducer", "wave-guide",
          "coils", "matrix", "sensors", "invertor"));
    A=A.replace("D", D, 1);
  while A.find("E")>=0:
    E=random.choice(("one", "two", "three", "four", "five"));
    A=A.replace("E", E, 1);
  line="Captain, "+A;
  return line;

def jeheetnu(newnick):
  while (len(newnick)<3):
    newnick=newnick+"-";
  return "NICK "+newnick;

def randomnaam(params):
  getdiscworldname=(random.random() > 0.5);
  if (getdiscworldname):
    try:
      getdiscworldname=(discwho("")=="niemand!")
    except:
      getdiscworldname=(1==0);
  if (getdiscworldname):
    #discworld name
    tn = telnetlib.Telnet('discworld.imaginary.com', 4242);
    tn.read_until("Your choice:");
    tn.write("n\n");
    tn.read_until("'g' for a list");
    tn.read_until("generated names:");
    tn.write("g\n");
    result=tn.read_until("Your choice?");
    result=string.split(result, '\n');
    categorynum=random.randint(1, 8);
    category=result[categorynum+1][4:];
    n=string.find(category, "(");
    if (n!=-1):
      category=string.strip(category[:n-1]);
  
    tn.write(string.digits[categorynum]);
    tn.write("\n");
    result=tn.read_until("Your choice?");
    tn.close();
    result=string.split(result, '\n');
    naam=string.strip(result[random.randint(1, 9)][4:]);
    #print("\nnaam \""+naam+"\" uit category \""+category+"\"\n");
  else:
    #http://www.ruf.rice.edu/~pound/ naam
    cmd="""wget -q -O - http://www.ruf.rice.edu/~pound |
           grep \"<li><a\" | grep \"sample out\"""";
    inp,outp,stderr = os.popen3(cmd);
    result = outp.read();
    outp.close();
    inp.close();
    stderr.close();
    result = string.split(result, '\n');
    line = random.choice(result);
    i1 = string.rfind(line, "=\"");
    i2 = string.rfind(line, "\">");
    url = "http://www.ruf.rice.edu/~pound/"+line[i1+2:i2];
    i1 = string.find(line, "\">");
    i2 = string.find(line, "</a>");
    category=line[i1+2:i2];
    cmd = "wget -q -O - "+url;
    inp,outp,stderr = os.popen3(cmd);
    result = outp.read();
    outp.close();
    inp.close();   
    stderr.close();
    result = string.split(result, '\n');
    naam=random.choice(result);
  return ("NICK %s\nik heb deze keer gekozen voor een naam uit de "+
      "categorie \"%s\"\n") % (naam, category);

if not(vars().has_key("remind_threads")):
  remind_threads=0;

def remind_thread(unused1, unused2):
  global remind_threads;
  if (remind_threads>0):
    print repr(remind_threads)+"th remind thread refusing to start";
    return;
  remind_threads+=1;
  try:
    while True:
      now=int(round(time.time()));
      print "remind thread: calculating sleep time (now="+repr(now)+")";
      next=now+(5*60);
      try:
        tijd=min(next,
            int(float(piet.db("SELECT MIN(tijd) from reminds")[1][0])));
      except:
        print "remind thread: geen reminds meer";
        break;
      print "remind thread: finished calculating sleep time";

      wachttijd=tijd-now;
      if (wachttijd>0):
        print "remind thread slaapt voor "+pietlib.format_tijdsduur(wachttijd);
        time.sleep(wachttijd);
      else:
        print "remind thread slaapt niet";

      print "remind thread: checking messages";
      try:
        now=int(round(time.time()));
        msgs=piet.db("SELECT channel,nick,msg,tijd FROM reminds "+
            "WHERE tijd<="+repr(now+1))[1:];
        for m in msgs:
          if (len(m)!=4):
            print "WARNING: malformed db response in remind: "+repr(m);
          if m[2][:4]=="zeg ":
            channel = m[0]
            zeg(m[2])
          else:
            telaat=now-int(float(m[3]));
            if (telaat>0):
              piet.send(m[0], "%s (ja, %s te laat)" %
                  (m[2], pietlib.format_tijdsduur(telaat)));
            else:
              piet.send(m[0], m[2]);
        piet.db("DELETE FROM reminds WHERE tijd<="+repr(now+1));
      except:
        #traceback.print_exc();
        pass;
      print "remind thread: finished checking messages";

  except:
    traceback.print_exc();
    print "onverwachte remind error: "+repr(sys.exc_info()[0]);
  
  print "remind_thread terminating";
  remind_threads-=1;

def remind(regel):
	try:
		if (regel[0:4]=="list"):
			return list_reminds(string.strip(regel[5:]))
	except:
		traceback.print_exc()
		return "frop"

	now = time.time()
	tz=pietlib.tijdzone_nick(nick);
	try:
		(tijd,result) = pietlib.parse_tijd(regel, tz)
		tijd = round(tijd - now)
	except:
		traceback.print_exc()
		return "volgens mij hou je me voor de gek, wat is dit voor rare tijd?"
	if (tijd<120):
		piet.send(channel, "dat is al over "+str(tijd) +
				" seconden! maar goed, ik zal herinneren\n")
	else:
		piet.send(channel, "goed, ik zal je waarschuwen. maar pas over " +
				pietlib.format_tijdsduur(tijd)+", hoor\n")
	if (tijd<5*60 and tijd>=0):
		chan = channel
		time.sleep(tijd)
		piet.send(chan, string.strip(parse(result, False, True)))
		return ""

	# meer dan 5 min, stop in db
	# CREATE TABLE reminds (channel string, nick string, msg string, tijd int)
	piet.db("INSERT INTO reminds VALUES(\""+
			string.replace(channel, '"', '""')+"\",\""+
			string.replace(nick, '"', '""')+"\",\""+
			string.replace(result, '"', '""')+"\","+
			repr(now+tijd)+");")
	piet.thread(channel, "remind_thread", "") # make sure a thread is running
	return ""
piet.thread(channel, "remind_thread", "")

def list_reminds(regel):
  try:
    qry="SELECT channel,nick,msg,tijd FROM reminds"
    if (regel!="all"):
      qry+=" WHERE nick=\""+nick+"\""
    qry+=" ORDER BY tijd"
    try:
      msgs=piet.db(qry)[1:]
    except:
      return "ik herinner je helemaal nergens aan.."

    now=int(round(time.time()))
    msg=[]
    for x in msgs:
      if len(x)==4:
        msg.append('over %s, "%s"' % (
            pietlib.format_tijdsduur(int(round(float(x[3])))-now), x[2]));
    return '\n'.join(msg);

  except:
    traceback.print_exc();
  return "";

def verklaar(regel):
  params=string.split(regel, ' ');
  if (len(params)<1) or (len(params[0])==0):
    return "zou eens een parameter toevoegen aan het commando"; 
  cmd = "lynx -dump \"http://www.googlism.com/index.htm?ism="+params[0]+"&type=1\" | grep -A 5000 Googlism\ for: | grep -B 5000 Travel\ \&\ Transportation | grep -v Googlism\ for: | grep -v Travel\ \&\ Transportation | head -n 6";
  inp,outp,stderr = os.popen3(cmd);
  result = outp.read();
  outp.close();
  inp.close();
  stderr.close();
  i = string.find(result,"[10]");
  if i<0:
    i=string.find(result,"[7]");
  if i>=0:
    return "zelfs het internet weet niet wat dat is";
  return result;

#emote functions
def mep(regel):
  params=string.split(regel,' ');
  if (len(params)<1) or (len(params[0])==0):
    return "ACTION mept er lustig op los";
  if (params[0]=="piet" or params[0]==piet.nick() or params[0]=="jezelf" or params[0]=="zichzelf"):
    return "ACTION heeft een hekel aan zichzelf, maar doet niet aan zelfverminking"
  r=random.random()
  if (r<=0.1):
    return "ik zou niet weten waarom"
  if (r<=0.2):
    return "ACTION mept "+nick+" zelf"
  if (r<=0.5):
    return "ACTION deelt een corrigerende mep uit aan "+params[0]
  return "ACTION mept "+params[0]

def geef(regel):
  params=string.split(regel,' ');
  if (len(params)<1) or (len(params[0])==0):
    return "ACTION geeft "+nick+" een blik van verstandhouding";
  before="";
  line="";
  for a in params:
    before+=a+" ";
    if a=="aan":
      line=before;
  if (line!=""):
    return "ACTION geeft "+before;
  return "ACTION deelt "+params[0]+" "+string.join(params[1:],' ')+" uit";

def dum(params):
  if len(params)>0:
    return "dum wat?";
  r=random.random();
  if (r<=0.2):
    return "die dum dum";
  if (r<=0.5):
    print "piet: verklaar dum"
    return "piet: verklaar dum\n"+verklaar("dum");
  return "dat jij je verveelt is ok, maar dan hoef je mij nog niet er mee te vermoeien";

def docommand(cmd):
  inp,outp = os.popen2(cmd);
  result = string.split(outp.read(), '\n');
  outp.close();
  inp.close();
  return result;


def tempwereld(regel):
  regel=string.lower(regel)
  regel=string.replace(regel,"\"new york\"","new_york");
  regel=string.replace(regel,"'new york'","new_york");
  regel=string.replace(regel,"new york","new_york");
  regel=string.replace(regel,"\"den haag\"","den_haag");
  regel=string.replace(regel,"'den haag'","den_haag");
  regel=string.replace(regel,"den haag","den_haag");
  regel=string.replace(regel,"\"zhong guo\"","hong_kong");
  regel=string.replace(regel,"'zhong guo'","hong_kong");
  regel=string.replace(regel,"zhong guo","hong_kong");
  regel=string.replace(regel,"\"hong kong\"","hong_kong");
  regel=string.replace(regel,"'hong kong'","hong_kong");
  regel=string.replace(regel,"hong kong","hong_kong");
  params=string.split(regel, ' ');
  if (len(params)<1) or (len(params[0])==0):
    params=string.split("enschede sydney",' ');
  result="";
  for City in params:
    City=string.replace(City,"\"","'");
    if (City=="e'de" or City=="enschede" or City=="twente" or City=="twenthe"):
      City="Enschede";
    elif (City=="r'dam" or City=="rotterdam"):
      City="Rotterdam";
    elif (City=="den_haag" or City=="d'haag"):
      City="Den Haag";
    elif (City=="j'burg" or City=="johannesburg"):
      City="Johannesburg";
    elif (City=="a'dam" or City=="amsterdam"):
      City="Amsterdam";
    elif (City=="h'kong" or City=="hong_kong") or (City=="z'guo"):
      City="Hong Kong";
    elif (City=="l'sum" or City=="loppersum"):
      City="Loppersum";
    elif (City=="y'burg" or City=="v'burg" or  City=="voorburg" or City=="ypenburg"):
      City="Ypenburg";
    elif (City=="l'rden" or City=="leeuwarden" or City=="reduzuum" or City=="r'zum"):
      City="Leeuwarden";
    elif (City=="nsw" or City=="sydney"):
      City="Sydney";
    elif (City=="cairns"):
      City="Cairns";
    elif (City=="h'sum" or City=="hilversum" or City=="hsum"):
      City="Hilversum";
    elif (City=="ny" or City=="new_york"):
      City="New York";
    elif (City=="arnhem"):
      City="Arnhem";
    elif (City=="p'burgh" or City=="pennsylvania" or City=="pittsburgh"):
      City="Pittsburgh";
    url="";

    cityurlmap=[
      ("Hong Kong","?ID=I90580993","HKT"),
      ("Ypenburg","?ID=IZUIDHOL11","CET"),
      ("Enschede","?ID=IOVERIJS5","CET"),
      ("Loppersum","?ID=IGRONING8","CET"),
      ("New York","?ID=KNYNEWYO17","EST"),
      ("Groningen","?ID=IGRONING9","CET"),
      ("Leeuwarden","?ID=IFRIESLA16","CET"),
      ("Sydney","?ID=INSWCHAT1","AEST"),
      ("Pittsburgh","?ID=KPAPITTS8","EDT"),
      ("Hilversum","?ID=IHILVERS3","CET"),
      ("Rotterdam","?ID=IZHROTTE2","CET"),
      ("Amsterdam","?ID=INOORDHO1","CET"),
      ("Cairns","?ID=IQUEENSL32","AEST"),
      ("Johannesburg","?ID=IGAUTENG8","SAST"),
      ("Den Haag","?ID=IZUIDHOL11","CET"),
      ("Arnhem","?ID=IGELDERL20","CET")];
    for (name,x,t) in cityurlmap:
      if name==City:
        url=x;
        timezone=t
    if (url==""):
      return "ken geen "+City;
    url="http://www.wunderground.com/weatherstation/WXDailyHistory.asp"+url
    cmd="wget -O - -q "+url;
    inp,outp,err=os.popen3(cmd);
    webresult=outp.read();
    inp.close(); outp.close(); err.close();
    i=string.find(webresult,"Your Lat")
    error=0
    templine="";
    if (i<=0):
      error=1
    else:
      i=string.rfind(webresult[:i],"rowW");
      if (i<=0):
        error=2
    if (error==0):
      i=string.find(webresult,"<td",i)+3;
      i=string.find(webresult,">",i)+1;
      j=string.find(webresult,"</td",i);
      tijd=webresult[i:j]+" "+timezone
      if (i<=0):
        error=3
    if (error==0):
      i=string.find(webresult,"<nobr",i)+1;
      i=string.find(webresult,"<nobr",i);
      if (i<=0):
        error=4
    if (error==0):
      i=string.find(webresult,"<b>",i)+3;
      j=string.find(webresult,"<",i);
      if (i<=0 or j<i):
        error=5
    if (error==0):
      templine=tijd+" "+City+", temp: "+webresult[i:j]+"°C, luchtvochtigheid: ";
      j=string.find(webresult,"%",j);
      j=string.rfind(webresult[:j],">")+1
      if (j<=0):
        error=6
    if (error==0):
      templine+=webresult[j:j+2]+"%, wind: ";
      i=string.rfind(webresult[:j],"km/h")-1;
      i=string.rfind(webresult[:i],"km/h");
      i=string.rfind(webresult[:i],"<nobr>")+6
      if (i<=0):
        error=7
    if (error==0):
      if (webresult[i:i+4]=="Calm"):
        templine+="rustig"
      else:
        i=string.find(webresult,"<b>",i)+3
        j=string.find(webresult,"<",i)
        templine+=webresult[i:j]+"km/h"
    if (error==0):
      result+="\n"+templine
    else:
      result+="\n"+City+", de site werkt niet mee ("+str(error)+")"
  return result;

def tempnl(params):
  plaats=string.lower(params);
  if plaats in ("h'sum", "hilversum", "arnhem"):
    plaats="de bilt";
  elif (plaats=="r'dam"):
    plaats="rotterdam";
  elif plaats in ("e'de", "enschede", "twente"):
    plaats="twenthe";
  elif plaats in ("a'dam", "amsterdam", "diemen", "dmz"):
    plaats="schiphol";

  cmd = "lynx -dump http://www.knmi.nl/actueel/ | sed -n '/Waarnemingen /,${s/[[:blank:]]\+/\t/g;s/^\t//;/\(\t.*\)\{4\}/p}'"
  cmd += "| sed 's/Den\tHelder/Den Helder/;s/De\tBilt/De Bilt/'";
  outp = os.popen(cmd);
  result=string.split(outp.read(), '\n');
  outp.close();
  result=[string.split(t, '\t') for t in result if len(t)>0];
  eenmap={};
  for a in result[1:]:
    eenmap[string.lower(a[0])]=a;
  
  myline=eenmap[plaats]; # gooit exceptie als plaats niet bestaat
  
  line="op "+string.join(result[0][1:], ' ')+" in "+string.lower(myline[0]);
  line+=": "+string.join(myline[1:][:-6])+" en "+myline[-6]+" graden. ";
  line+="de wind waait met "+myline[-3]+"m/s uit het "+myline[-4]+" en ";
  line+="je kunt "+myline[-2]+"m ver zien.";
  return line;

def temp(params):
  try:
    line=tempnl(params);
  except:
    line=tempwereld(params);
  return line;

def wiki(regel):
  params=string.split(regel, ' ');
  if (len(params)<1) or (len(params[0])==0):
    return "Misschien wil je wel eens een wiki parameter doen?";
  else:
    regel = string.strip(parse(regel, False, True));
    params=string.split(regel,' ');    
  regel = string.strip(string.join(params,"%20"));
  cmd = "lynx -dump http://nl.wikipedia.org/w/wiki.phtml?search="+regel+"  |"+\
        "grep -A 20 Overeenkomst\ met\ v | grep -B 20 Overeenkomst\ met\ a |"+\
        "grep \"bytes)\"";
  inp,outp,stderr = os.popen3(cmd);
  result = outp.read();
  outp.close();
  inp.close();
  stderr.close();
  result = string.split(result,'\n');
  returnline="";
  newurl="";
  if (len(result)>1):
    returnline="Ik heb de volgende items gevonden:";
    for a in result:
      a=string.split(a,']');
      if (len(a)>1):
        a=string.split(a[1],'(');        
        returnline+="\n"+a[0];
        if string.join(a[0].strip().split(' '),"%20").lower()==regel.lower():
          newurl="http://nl.wikipedia.org/wiki/"+a[0].strip().replace(' ','_');
  if (newurl==""):
    return returnline;
  cmd = "wget -O - -q "+newurl;
  inp,outp,stderr = os.popen3(cmd);
  result = outp.read();
  outp.close();
  inp.close();
  stderr.close();
  i = string.find(result,"<h1");
  i = string.find(result,"<p>",i);
  result=result[i:];
  while (string.find(result,"<table") > 0):
    s = string.find(result,"<table");
    e = string.find(result,"</table")+8; 
    result = result[:s]+result[e:];
  result=result[:string.find(result,"<p>",500)];
  result="<html><body>"+result+"</body></html>";
  f=open('temp', 'w');
  f.write(result);
  f.close();
  cmd="lynx temp -force_html -dump; rm temp";
  inp,outp,stderr = os.popen3(cmd);
  result = outp.read();
  outp.close();
  inp.close(); 
  stderr.close();  
  if string.find(result,"Reference") > 0:
    result = result[:string.rfind(result,"Reference")];
  toreturn = "";
  for line in string.split(result,'\n'):
    toreturn += string.strip(line)+'\n';
  return string.strip(toreturn);


def temp2(regel):
	print repr(regel)
	regel = regel.strip()
	if not(regel):
		raise pietlib.piet_exception("het is lekker knus en warm hier in m'n computerkast")
	splitpos=regel.find(' ')
	if regel[:8].lower()=="den haag":
		splitpos=8
	if splitpos>0:
		reqcity,rest = regel[:splitpos], regel[splitpos+1:]
	else:
		reqcity,rest = regel, ""
	recurse_result=""
	print repr((reqcity, rest, splitpos, regel))
	if rest:
		recurse_result = temp2(rest)

	aliases = {
		"h'sum": "hilversum",
		"sydney": "sydney,au",
		"e'de": "enschede",
		"d'haag": "den haag",
		"r'dam": "rotterdam",
		"den_haag": "den haag",
		"vb": "voorburg",
		"vburg": "voorburg",
		"reduzum": "roordahuizum"}
	if reqcity in aliases:
		reqcity = aliases[reqcity]
	if reqcity.find(',')<0:
		reqcity = reqcity+",nl"
	reqcity = reqcity.replace("_", " ")
	reqcity = reqcity.replace(", ", ",")

	form = { 'submit': 'GO', 'u': '1', 'partner': 'accuweather' }
	form['loccode']=reqcity
	a = pietlib.get_url('http://www.accuweather.com/world-index-forecast.asp?'+ urllib.urlencode(form))

	current_temp = (re.findall('<div id="quicklook_current_temps">([^<]*)', a) or [""])[0].replace('&deg;', " graden ")
	current_feeltemp = (re.findall('<div id="quicklook_current_rfval">([^<]*)', a) or [""])[0].replace('&deg;', " graden ")
	current_weather = (re.findall('<div id="quicklook_current_wxtext">([^<]*)', a) or [""])[0].replace('&deg;', " graden ")
	t = (re.findall('<a id="quicklook_curr_head"[^>]*>.* ([0-9]+:[0-9]+.*)</a>', a) or [""])[0]
	t2 = re.match('([0-9]+):([0-9]+)([AP])M', t)
	if t2:
		h,m,c = t2.groups()
		if c=='P' and int(h)<12:
			h=int(h)+12
		if c=='A' and int(h)==12:
			h=int(h)-12
		t = "%d:%s" % (int(h),m)
	wind = (re.findall('Winds: ([\w]+).*at ([\w/]+)', a) or [("", "")])[0]
	city,country = (re.findall('<a [^>]*class="cityTitle"[^>]*>([^,]+), ([\w]+)', a) or [("", "")])[0]
	hum = (re.findall('Humidity: ([0-9]+)%', a) or [""])[0]
	if not(city):
		return reqcity+" ken ik niet, misschien een landcode erbij?\n"+recurse_result

	retries=2
	succes=None
	while not(succes) and retries>0:
		succes=1
		retries = retries -1

		current_weather = current_weather.lower()
		current_weather = (current_weather
				.replace("partly", "gedeeltelijk")
				.replace("mostly", "vooral")
				.replace("cloudy", "bewolkt")
				.replace("overcast", "bewolkt")
				.replace("lgt.", "lichte ")
				.replace("light", "lichte")
				.replace("hvy.", "zware ")
				.replace("rainshower", "buien")
				.replace("rain", "regen")
				.replace("sunny", "zonnig")
				.replace("snow", "sneeuw")
				.replace("thunderstorm", "onweer mogelijk met regen")
				.replace("thundershower", "kort onweer met zware regen")
				.replace("shower", "bui")
				.replace("dense fog", "dichte mist")
				.replace("ground fog", "mist aan de grond")
				.replace("fog", "mist")
				.replace("foggy", "mistig"))

		timezone = None
		if country=="Netherlands":
			timezone = 'Europe/Amsterdam'
		elif country=="Australia":
			timezone = 'Australia/Sydney'

		print "tijd op pagina voor %s was %s" % (city, t)
		#t2 = re.match('^([0-9]+):([0-9]+)$', t)
		#if timezone and t2: # convert the time on page to relative time for the user
		#	os.environ['TZ'] = timezone;
		#	time.tzset();
		#	ts = time.localtime()
		#	pietlib.timezone_reset()
		#	h_diff = ts.tm_hour - int(t2.group(1))
		#	if h_diff<0: h_diff=h_diff+24
		#	m_diff = ts.tm_min - int(t2.group(2))
		#	if m_diff<0:
		#		m_diff=m_diff+60
		#		h_diff=h_diff-1
		#	dur = (h_diff * 60 + m_diff) * 60.0
		#	print (h_diff, m_diff, dur)
		#	if dur>=14340 and dur==14400:
		#		piet.send(channel, "prutssite is europa nog even aan het zoeken, ik probeer zo weer")
		#		time.sleep(10)
		#		succes=None
		#	if dur<-5*60:
		#		t=', '+t+'\x02(lokale tijd, toekomst!)\x02'
		#	elif dur<0:
		#		t=", over "+pietlib.format_tijdsduur(dur, 1)
		#	elif dur<5*60:
		#		t=""#pietlib.format_tijdsduur(dur, 1) +" geleden"
		#	else:
		#		t=', \x02'+pietlib.format_tijdsduur(dur, 2) +" geleden\x02"
		#else:
		#	t=", om "+t+'(lokale tijd)'

	line = "%s, %s, wind uit %s, %s, %s rel %% vochtigheid, %s" % (
			city, current_temp, wind[0], wind[1], hum, current_weather)
	return line+"\n"+recurse_result


def find_xml_block(page, tag):
	""" returns the block within the first <tag>..</tag> """
	lpage = page.lower()
	tag = tag.lower()
	begin = lpage.find("<%s>" % tag)
	if begin < 0:
		raise Exception("no tag <%s> found on page" % tag)
	end = page.find("</%s>" % tag, begin)
	if end < 0:
		raise Exception("no end tag </%s> found on page" % tag)
	return page[begin+len(tag)+2:end]

def temp3(params):
	form = { 'hl':'nl', 'weather':params.strip() }
	page = pietlib.get_url('http://www.google.com/ig/api?' + urllib.urlencode(form))

	info = find_xml_block(page, "forecast_information")
	dinfo = dict(re.findall('<([^ ]*) data="([^"]*)"/>', info))

	cur = find_xml_block(page, "current_conditions")
	d = dict(re.findall('<([^ ]*) data="([^"]*)"/>', cur))

	city = dinfo['city'].split(',')[0]
	tijd = dinfo['current_date_time']
	tijd = time.strptime(tijd, "%Y-%m-%d %H:%M:%S +0000")
	tijd = calendar.timegm(tijd) # now in secs since epoch
	now = time.time()
	tijdswaarschuwing = ''
	if now-tijd > 15*60:
		tijdswaarschuwing = ", %s geleden" % pietlib.format_tijdsduur(now-tijd,1)

	humidity = d['humidity'].split()[-1]
	wind = d['wind_condition'].split(': ')[-1]
	r = "%s%s: %s, %s graden, wind %s, vochtigheid %s" % (city, tijdswaarschuwing, d['condition'], d['temp_c'], wind, humidity)
	return r.lower()


def commando_tijd(regel):
  if len(regel)>0:
    try:
      tz=find_timezone(regel, 0);
      os.environ['TZ']=tz;
      time.tzset();
      t=time.strftime("%H:%M", time.localtime());
      pietlib.timezone_reset();
      return "in "+tz.lower()+" is het "+t;
    except:
      return "kies eens een andere tijdzone ofzo, wat een onzin"

  inp=piet.db('SELECT name,timezone FROM auth');
  if (inp==None or len(inp)<=1): # no users
    return time.strftime("%H:%M", time.localtime());

  # inp[1:] = [[naam,tijdzone]]
  tzs=set([tz for n,tz in inp[1:]]);
  tzcalc={};
  for tz in tzs:
    os.environ['TZ']=tz;
    time.tzset();
    tzcalc[time.strftime("%H:%M", time.localtime())]=tz;
  # tzcalc is mapping van tijd naar tijdzone

  # zoek lokale tijd op, die moet voorop
  pietlib.timezone_reset();
  result=time.strftime("%H:%M", time.localtime());
  if (tzcalc.has_key(result)): del tzcalc[result];

  result="bij mij is het "+result;
  for t,tz in tzcalc.iteritems():
    result=result+", en in "+tz.lower()+" is het "+t;
  return result+"\n";

def find_timezone(param, verbose):
  path='/usr/share/zoneinfo/';
  try:
    if (stat.S_ISREG(os.stat(path+param).st_mode)):
      return param;
  except:
    pass;
  param=param.lower();
  submatch=[];
  fullmatch=[];
  for root, dirs, files in os.walk(path):
    files=[i for i in files if i.lower().find(param)>-1];
    root=root[len(path):];
    if len(root)>0: 
      root=root+"/";
    for i in files:
      submatch.insert(999, root+i);
    files=[i for i in files if i.lower()==(param)];
    for i in files:
      fullmatch.insert(999, root+i);
  if len(fullmatch)>0:
    if len(fullmatch)>0 and verbose:
      piet.send(channel,"hmm, ik kan kiezen uit "+pietlib.make_list(fullmatch));
    fullmatch.sort(lambda x,y: cmp(len(x),len(y)));
    return fullmatch[0];
  if len(submatch)>0:
    if len(submatch)>0 and verbose:
      piet.send(channel,"hmm, ik kan kiezen uit "+pietlib.make_list(submatch));
    submatch.sort(lambda x,y: cmp(len(x),len(y)));
    return submatch[0];
  raise "onbekende tijdzone";

def tijdzone(regel):
  a=string.split(regel, ' ');
  if (a==None or len(a)==0 or len(a[0])==0):
    matches=piet.db('SELECT name,timezone FROM auth');
    if (len(matches)<2): return "ik ken helemaal niemand!";
    s={};
    for n,tz in matches[1:]:
      if (tz in s):
        s[tz]=s[tz]+", "+n;
      else:
        s[tz]=n;
    return string.join([tz+": "+ns for tz,ns in s.iteritems()], '\n');
  elif (len(a)==1):
    tz=pietlib.tijdzone_nick(a[0]);
    return a[0]+" huppelt rond in "+tz+"\n";
  elif(len(a)==2):
    try:
      tijdzone=find_timezone(a[1], 1);
    except:
      traceback.print_exc();
      return "sorry, ik doe alleen tijdzones van de planeet aarde\n";

    oldauth=piet.db('SELECT auth FROM auth WHERE name="'+a[0]+'"');
    if not(oldauth) or len(oldauth)<2: # no result or only header
      piet.db('REPLACE INTO auth(name,timezone) VALUES("%s","%s")' %
          (a[0], tijdzone));
    else:
      oldauth = int(oldauth[1][0]);
      piet.db('REPLACE INTO auth(name,auth,timezone) VALUES("%s",%d,"%s")' %
          (a[0], oldauth, tijdzone));

    if tijdzone==a[1]:
      return \
        "zozo, jij kent je tijdzones goed. ik zet "+a[0]+" in "+tijdzone+"\n";
    else:
      return \
        "ik zet "+a[0]+" wel in "+tijdzone+", dat lijkt wel wat op "+a[1]+"\n";
  return "zeges, tiepgraag mannetje, 2 parameters is echt 't maximum hoor\n";

def quote(regel):
  a=string.split(regel, ' ');
  if (len(a)==1):
    if (a[0]=="add"):
      return "te weinig tekst om toe te voegen aan de quote list";
    inf = open("quote.txt");
    lines = string.split(inf.read(), '\n');
    lines=lines[0:len(lines)-1];
    inf.close();
    return random.choice(lines)+"\n";
  if (a[0]=="add"):
    regel=string.strip(string.join(a[1:]," "));
    inf = open("quote.txt");
    lines = inf.read();
    inf.close();
    lines=lines+regel+"\n";
    outf=open("quote.txt","w");
    outf.write(lines);
    outf.close();
    return 'toegevoegd: "%s"' % regel
  return "Syntax is fout voor quote";

def tv_nuenstraks(params):
  soup=pietlib.get_url_soup("http://www.tvgids.nl/nustraks/");
  t=soup('div', {'id' : 'nuStraks'})[0].div.form.table;
  needed=("Nederland 1", "Nederland 2", "Nederland 3", "RTL 4", "RTL 5",
      "SBS 6", "NET 5", "RTL 7", "Talpa", "Veronica");
  r="";
  for i in t('tr')[1:]:
    td=i('td');
    th=i('th');
    chan=str(td[0].span.string);
    if (chan in needed):
      line="  "+chan+", "+str(td[1].div.a.string);
      if (th[1].contents[0]!=None):
        line=line+", om "+str(th[1].string)+" "+str(td[3].div.a.string);
      else:
        line=line+", en daarna niks meer";
      r=r+line+"\n";
  return r;

def topic_cmds(params):
	global topic
	cmd = params.split(' ', 1)[0].lower()

	if not(topic):
		raise pietlib.piet_exception("ik weet niks van 't topic, vraag het "+
				random.choice([ i for i in nicks.keys() if i!=piet.nick()] or ["sinterklaas"])+
				" eens")

	if cmd in ["history", "geschiedenis", "his"]:
		nu = time.time()
		lines = [ "%s geleden, %s" % (pietlib.format_tijdsduur(nu-t), line) for (t,line) in reversed(topic) ]
		return '\n'.join(lines)
	elif cmd in ["get", "toon", "view", "tonen"]:
		return "volgens mij is de topic: "+topic[-1][1]
	elif cmd in ["set", "reset"]:
		return "TOPIC "+topic[-1][1]
	elif cmd in ["pop"]:
		if len(topic)==1:
			raise pietlib.piet_exception("ik weet de vorige topic niet")
		topic.pop()
		(oldtijd, oldtopic) = topic[-1]
		tz = pietlib.tijdzone_nick(nick)
		return "ok, ik zet de topic van "+pietlib.format_localtijd(oldtijd, tz
				)+" terug\nTOPIC "+topic[-1][1]
	else:
		return "ja? wat moet ik met de topic? 'tonen'? 'reset'ten? wil je de 'geschiedenis' zien? of zal ik een topic van de stapel 'pop'en?"


def trigram_grow_back(cur):
  last3wordsmatch=re.search("(([\w/\\'`]+[\s,]+){0,1}[\w/\\'`]+)$", cur);
  last3words = cur[last3wordsmatch.start():last3wordsmatch.end()];
  prefix = cur[:last3wordsmatch.start()];
  qry='SELECT line FROM log WHERE line like "%'+last3words+'%" LIMIT 50';
  matches=(piet.db(qry) or [])[1:];
  if (len(matches)==0): return (cur, False);
  newphrase=[re.findall(last3words+"[\s,]+[\w/\\'`]+", i[0]) for i in matches];
  newphrase=[i[0] for i in newphrase if len(i)>0];
  if (len(newphrase)==0): return (cur, False);
  line=prefix+random.choice(newphrase);
  return (line,True);

def trigram_grow_front(cur):
  first3wordsmatch=re.search("^(([\w/\\'`]+[\s,]+){0,1}[\w/\\'`]+)", cur);
  first3words = cur[first3wordsmatch.start():first3wordsmatch.end()];
  postfix = cur[first3wordsmatch.end():];
  qry='SELECT line FROM log WHERE line like "%'+first3words+'%" LIMIT 50';
  matches=(piet.db(qry) or [])[1:];
  if (len(matches)==0): return (cur, False);
  newphrase=[re.findall("[\w/\\'`]+[\s,]+"+first3words, i[0]) for i in matches];
  newphrase=[i[0] for i in newphrase if len(i)>0];
  if (len(newphrase)==0): return (cur, False);
  line=random.choice(newphrase)+postfix;
  return (line, True);

def trigram(woord):
  if (len(woord)==0):
    rowcount=int(piet.db("SELECT count(*) from log")[1][0]);
    qry="SELECT line from log where ROWID=ABS(RANDOM()%"+str(rowcount)+")";
    line=piet.db(qry)[1][0];
    woord=random.choice(re.findall("[\w/\\'`]+", line));
  ok=True;
  while(ok):
    (woord,ok)=trigram_grow_back(woord);

  ok=True;
  while(ok):
    (woord,ok)=trigram_grow_front(woord);
  return woord;

def mytest(regel):
  piet.db("PRAGMA temp_store=2");
  return "result: "+repr(piet.db(regel))+"\n";

def tel(regel):
	if not(regel):
		result=piet.db("SELECT naam,nummer FROM telefoonnrs")[1:]
		if not(result):
			return "geef eens een naam ofzo"
		result = ["%s: %s" % (i,j) for i,j in result ]
		return "\n".join(result)
	result = db_get('telefoonnrs', 'naam', regel, 'nummer')
	if result:
		return "ah! die weet ik! "+regel+" is bereikbaar op "+result

	params = shlex.split(regel)
	i=0
#parse naam argument
	naam="";
	if (len(params)<1) or (len(params[0])==0):
		return "mis naam argument";
	else:
		naam=params[i];
	i+=1;

#parse plaats argument
	plaats="";
	if (len(params)==i):
		return "mis plaats argument";
	else:
		plaats=params[i];
	soup = pietlib.get_url_soup("http://mobiel.detelefoongids.nl/frontpage.seam",
			postdata={'lang':'nld', 'new':'1', 'index':'0', 'rq':'', 'lockey':'', 'white':'Zoek',
			'UMP_FORM_ACTION':'aHR0cDovL3BvcnRhbC1hcHAudW53aXJlLmRrL2Vkc2EvcmVzdWx0cGFnZS5zZWFt',
			'PORTAL_SERVER_ENCODING':'UTF-8',
			'what':naam, 'where':plaats})
	# geen idee wat die UMP_FORM_ACTION cruft is
	result = soup.findAll('div', {'class':'searchResultInfo'})

	if not result:
		return "Volgens de telefoongids woont er geen %s in %s, sorry" % (naam,plaats)

	namen = soup.findAll('div', {'class':'searchWhiteResultHeader'})
	namen = [ str(i.a.string) for i in namen ]
	notags = lambda x: re.sub('<[^>]*>', '', str(x)).replace('&nbsp;', ' ')
	fresult = ''
	for n,r in zip(namen,result):
		r = notags(r).replace('\t',' ').replace('\xc2\xa0',' ').split('\n')
		fresult += "%s, %s, %s\n" % (n, r[1], r[4].strip())
	return fresult;    

def geoip(params):
  params=string.split(params," ")
  if (len(params)<1) or (len(params[0])==0):
    return "Heb een ip-adres nodig"
  address=params[0].split(".")
  if len(address)!=4:
    return "syntax ip adres is X.X.X.X"
  for i in address:
    try:
      if int(i)<0 or int(i)>255:
        return "syntax is X.X.X.X met 0<=X<=255"
    except:
      return "syntax ip adres is X.X.X.X"
  cmd="echo ipaddresses="+params[0]+" | lynx -post_data http://www.ip2location.com/free.asp"
  inp,outp,stderr = os.popen3(cmd);
  result = outp.read();
  outp.close();
  inp.close();
  stderr.close();
  i=result.find("Map")
  i=result.find("\n",i)
  while result[i:i+1]==" ":
    i+=1
  n=result.find("These results",i)
  result=result[i:n]
  returnvalue=""
  t=0
  for x in result.split(" "):
    if x!="" and x!=" " and x[0:1]!="[":
      t+=1
      if t!=2:
        returnvalue+=x+" "
  return returnvalue.lower().strip()

def opme(params):
  piet.names(channel);
  return "ik zal eens kijken hoe het er hier voor staat en zo nodig actie "+\
    "ondernemen\n";

def ov9292_wrapper(params):
  return ov9292.ov9292(params,nick,channel);

def reloadding(params):
  params=string.split(params," ")
  def do_reload(lib):
    reload(lib)
    if lib.__dict__.has_key("piet_init"):
      lib.piet_init(functions)

  if (len(params)<1) or (len(params[0])==0):
    return "reload wat?"
  else:
    if params[0] in ("calc", "supercalc"):
      do_reload(calc)
      return "'t is vast gelukt";
    if params[0] in ("distance", "Distance"):
      do_reload(Distance)
      return "Distance lib ready to go";
    elif params[0]=="pistes":
      do_reload(pistes);
      return "och, wie weet is't gelukt";
    elif params[0]=="vandale":
      do_reload(vandale);
      return "och, wie weet is't gelukt";
    elif params[0]=="bash":
      do_reload(bash);
      return "kheb vast gereload";
    elif params[0]=="pietlib":
      do_reload(pietlib);
      return "tjip, een nieuwe lib!";
    elif params[0]=="gps":
      do_reload(gps);
      return "gps module good to go!";
    elif params[0] in ("ov9292", "ov"):
      do_reload(ov9292);
      return "_ov_ernieuw ingelezen!";
    elif params[0] in ("ns"):
      do_reload(ns);
      return "ns ingelezen!";
    elif params[0] in ("kook", "kookbalans"):
      do_reload(kookbalans);
      return "ok, gedaan";
  return "die module ken ik niet"


def meer(params):
  a=meer_data[nick];
  if a and len(a)>0:
    return string.join(a, '\n');
  return "nah"

def kookbalans_kookbalans(cmd):
  return kookbalans.cmd_kookbalans(channel,nick,auth,cmd)
def kookbalans_gekookt(cmd):
  return kookbalans.cmd_gekookt(channel,nick,auth,cmd)
def kookbalans_undo(cmd):
  return kookbalans.cmd_undo(channel,nick,auth,cmd)


def filemeldingen(params):
  result=pietlib.get_url("http://www.trafficnet.nl/traffic.asp?region=lijst")
  if params=="":
    i1=string.find(result,"textplain")
    i1=string.find(result,">",i1)+1
    i2=string.find(result,"<",i1)
    answer=string.replace(result[i1:i2],"&nbsp;"," ")+"\n"
    i1=string.find(result,"textplain",i2)
    i1=string.find(result,">",i1)+1
    i2=string.find(result,"<",i1)
    answer+=string.replace(string.strip(result[i1:i2]),"&nbsp;"," ")+"\n"
    wegenlijst=[]
    i1=string.find(result,"wegNrA",i1)
    if string.find(result,"<strong>",i1)<0:
      i1=-1
    while i1>0:
      i1=string.find(result,">",i1)+1
      i2=string.find(result,"<",i1)
      wegenlijst.append(result[i1:i2])
      i1=string.find(result,"wegNrA",i1)
      if string.find(result,"<strong>",i1)<0:
        i1=-1
    if not(len(wegenlijst)):
      return string.strip(answer)
    wegenlijst = list(set(wegenlijst))
    try:
      wegenlijst.sort(lambda x,y: cmp((x[0],int(x[1:])), (y[0],int(y[1:]))))
    except:
      traceback.print_exc();
    return answer+"Files op: "+(' '.join(wegenlijst))
  i1=string.find(result,"wegNrA")
  if string.find(result,"<strong>",i1)<0:
    i1=-1
  params=string.split(string.lower(params))
  answer=""
  while i1>0:
    i1=string.find(result,">",i1)+1
    i2=string.find(result,"<",i1)
    if string.lower(result[i1:i2]) in params:
      answer+=result[i1:i2]+": "
      s1=string.find(result,"<strong>",i1)+8
      s2=string.find(result,"<",s1)
      answer+=result[s1:s2]
      s1=string.find(result,">",s2)+1
      s1=string.find(result,">",s1)+1
      s2=string.find(result,"</",s1)
      desc=result[s1:s2]
      for item in string.split(desc,"\n"):
        answer+=item.replace("&nbsp;"," ").replace("<br>"," ").strip()+" ";
      answer+="\n"
    i1=string.find(result,"wegNrA",i1)
    if string.find(result,"<strong>",i1)<0:
      i1=-1
  answer=string.replace(answer,"  "," ")
  answer=string.replace(answer,"  "," ")
  if answer=="":
    return "Alles lijkt daar fijn te zijn"
  return answer

def versie(regel):
  regel=regel.lower().strip();
  if regel in ("centericq", "cicq"):
    result=pietlib.get_url("http://www.centericq.de/").lower();
    version=re.search("centericq ([0-9]+.[0-9]+.[0-9]+)", result)
    if version:
      return "Laatste Centericq versie "+version.group(1)
    return "Kan het versie nummer van Centericq niet vinden"
  if regel[:5]=="linux":
    result=pietlib.get_url("http://kernel.org/kdist/rss.xml").lower();
    version=re.search("([0-9]+.[0-9]+.[0-9]+(.[0-9]+)?): stable", result)
    if version:
      return "Laatste linux kernel versie "+version.group(1)
    return "Kan het laatste versie nummer van de linux kernel niet vinden"
  if len(regel)==0:
    return "ik ben nu versie %d.%d, maar dat kan straks wel anders wezen" % (
      random.randint(0,9),random.randint(0,9));
  return regel+" ken ik niet"

def formeer(regel):
  seats=0  
  partijen=[("cda","CDA",41),("pvda","PvdA",33),("vvd","VVD",22),("sp","SP",25),("cu","CU",6),("sgp","SGP",2),("pvdv","PvdV",9),("gw","PvdV",9),("wilders","PvdV",9),("gl","Groen Links",7),("d66","D66",3),("groen","Groen Links",7),("unie","CU",6),("arbeid","PvdA",33),("fortuyn","Fortuyn",0),("lpf","Fortuyn",0),("dieren","PvdD",2)]
  regel=regel.lower()
  result=""
  for (partij,check,zetels) in partijen:
    while (regel.find(partij)>=0):
      i=regel.find(partij)
      regel=regel[:i]+regel[i+3:]
      seats+=zetels
      result+=check+"_"
  if (result[len(result)-1:])=="_":
    result=result[:len(result)-1:]
  result=string.replace(result,"_",", ")
  return str(seats)+" zetels voor "+result

def verveel(regel):
  l = ("verbergen", "kijken", "verbieden", "huiswerk maken", "luisteren",
  "werken", "delen", "Kloppen op", "storen", "teruggeven", "vragen", "geven",
  "bezweren", "verzinnen", "slecht zijn", "slagen", "zin hebben",
  "van mening veranderen", "laten vallen", "deelnemen aan", "koken", 
  "de afwas doen", "lezen", "bezoeken", "knutselen", "bouwen", "tekenen",
  "maken", "zich inschrijven", "bewaren", "printen", "kopi\xebren",
  "op het web surfen", "verbonden zijn", "ontvangen", "sturen", "praten",
  "besturen", "vliegen", "nodig hebben", "voorstellen", "opletten",
  "lenen aan", "straf hebben", "mopperen", "waarschuwen", "klaar zijn",
  "denken aan", "een zwak hebben voor", "meten", "dragen", "verlaten",
  "lijken op", "bang zijn voor", "gelijk hebben", "worden",
  "een geintje maken", "spotten met", "tegen zijn", "optellen", "onthouden",
  "(op)zoeken", "volgen", "kiezen", "vergeten", "ruzie maken", "straffen",
  "schrijven", "inhalen", "wegsturen", "te laat zijn", "eisen", "bestaan",
  "verzocht worden om", "beginnen", "opnieuw beginnen", "stellen",
  "aankruisen", "het examen halen", "uitslapen", "kletsen", "zich orienteren",
  "informatie verzamelen", "sparen", "besteden", "betalen", "winnen",
  "verliezen", "stelen", "rijden");
  return "anders ga je %s" % random.choice(l);

def test_encoding(regel):
		piet.send(channel, "utf8: "+chr(0xc3)+chr(0x88))
		piet.send(channel, "iso8859: "+chr(200))
		return "E met backtick erop"


def prime(n):
	if(n==1):           # 1 is not prime so return false
		return False
	if(n==2):           # 2 is prime so return true
		return True
	if(not n%2):        # If the number is divisible by 2 the number is not prime
		return False
	for i in xrange(3,int(math.sqrt(n))+1,2): # Check for divisibility by each odd number from 3 to sqrt(n)
		if(not n%i):    # The number is divisible by some number so it is not prime.
			return False
	return True 


def factorize(n,l):         # n is the number to be factorized, l is a list which holds the prime factors
	for i in xrange(2,int(math.sqrt(n))+1): # Check each number from 2 to sqrt(n)
		if(not n%i):        # Some number i divides n
			if(prime(i)):   # If it is prime then append it to the list
				l.append(i)
			else:
				factorize(i,l) # If it is not prime then find the prime factors of that number 
			if(prime(n/i)):    # If the quotient is prime then append it to the list 
				l.append(n/i)
			else:
				factorize(n/i,l) # If the quotient is not prime then find the prime factors of the quotient.
			break


def factor(regel):
	if regel[:2] == 's ':
		regel = regel[2:]
	try:
		nr = int(regel)
	except:
		try:
			nr = int(calc.supercalc(regel))
		except:
			return "ongeveer 3"
	factors = []
	factorize(nr, factors)
	factors = [ str(i) for i in factors ]
	return "factors: "+pietlib.make_list(factors)


def utc(regel):
	regel = regel.strip()
	tz = pietlib.tijdzone_nick(nick)
	if not regel:
		t = time.time()
		return "het is nu %s, dat is in utc: %d" % (pietlib.format_localtijd(t, tz), t)
	elif re.match('1[0-9]{9}([.][0-9]+)?', regel):
		t = float(regel)
		t = pietlib.format_localtijd(t, tz)
		return "dat is %s in jouw tijdzone" % t
	else:
		try:
			(t, remainder) = pietlib.parse_tijd(regel, tz)
			if len(remainder):
				return "ik kon niks maken van "+repr(remainder)
		except:
			traceback.print_exc();
			return "sorry, ik snap je tijd niet"
		return "%s is in utc: %d" % (pietlib.format_localtijd(t, tz), t)



functions = {
# loos
    "anagram":           ("loos", 100, anagram, "bedenk een anagram, gebruik anagram <woorden> of anagram en <woorden> om engels te forceren."),
    "galgje":            ("loos", 150, galgje, "spel een spelletje galgje, begin met galgje start en daarna galgje raad <letter>"),
    "ping":              ("loos", 100, ping, "ping, zeg pong"),
    "PING":              ("loos", 100, ping, ""),
    "hallo?":            ("loos", 100, ping, ""),
    "spreuk":            ("loos", 0, spreuk, "spreuk, geef een leuke(?) spreuk"),
    "oneliner":          ("loos", 0, spreuk, ""),
    "dvorak2qwerty":     ("loos", 0, dvorak2qwerty, "dvorak2qwerty <text>, maak iets dat op een qwerty-tb in dvorak is getikt leesbaar"),
    "qwerty2dvorak":     ("loos", 0, qwerty2dvorak, "qwerty2dvorak <text>, maak iets dat op een dvorak-tb in qwerty is getikt leesbaar"),
    "achteruit":         ("loos", 0, reverse, "achteruit <text>, draait de tekst om"),
    "reverse":           ("loos", 0, reverse, ""),
    "d2q":               ("loos", 0, dvorak2qwerty, ""),
    "q2d":               ("loos", 0, qwerty2dvorak, ""),
    "leet":              ("loos", 0, leet, "leet <text>, convert to 1337"),
    "unleet":            ("loos", 0, unleet, "unleet <text>, unconvert to 1337"),
    "geordi":            ("loos", 0, geordi, ""),
    "citaat":            ("loos", 100, citaat, "citaat, geeft een random regel text die ooit gezegd is"),
    "pistes":            ("loos", 100, pistes.cmd_pistes, "pistes, doet iets met skipistes"),
    "weekend?":          ("loos", 100, weekend, ""),
    "url":               ("loos", 100, commando_url, "geef willekeurige oude url"),
    #"tv":                ("loos", 100, tv_nuenstraks, "geef overzicht van wat er op tv is"),
    "tv":                ("loos", 100, lambda x: "weer niks", "geef overzicht van wat er op tv is"),
    "trigram":           ("loos", 1000, trigram, "praat nonsens"),
    "bash":              ("loos", 100, bash.bash, "Geef bash quote <nummer> terug of een random bashquote bij gebrek aan nummer"),
    "sentence":          ("loos", 100, random_sentence, "sentence, geef een willekeurige engelse zin"),
    "dum":               ("loos", 0, dum, ""),
    "verveel":           ("loos", 100, verveel, "geeft een voorstel voor een activiteit"),
    "quote":             ("loos", 1000, quote, "quote <add> <regel> om iets toe te voegen of quote om iets op te vragen"),
    "kunstje":           ("loos", 100, lambda x: "nee, prutser, er bestaat geen 'kunstje' commando", ""),
    "trukje":            ("loos", 100, lambda x: "nee, prutser, kunstje", ""),
    "truckje":           ("loos", 100, lambda x: "nee, prutser, kunstje", ""),

# dicts
    "verklaar":          ("dicts", 100, verklaar, "Zoekt op het internet wat <regel> is"),
    "vandale":           ("dicts", 100, lambda x: vandale.LookUp(x), "vandale <woord>, zoek woord op in woordenboek"),
    "urban":             ("dicts", 100, urban, "urban <woord>, zoek woord op in urbandictionary (warning: explicit content)"),
    "rijm":              ("dicts", 100, rijm, "rijm <woord>, zoek rijmwoorden op"),
    "vertaal":           ("dicts", 100, vertaal, "vertaal <brontaal> <doeltaal> <regel>, vertaalt <regel> van de taal <brontaal> naar de taal <doeltaal>"),
    "afk":               ("dicts", 100, afk, "afk <afk>, zoek een afkorting op"),
    "spel":              ("dicts", 0, spell_nl, "spel <woord/zin>, spellcheck een woord/zin in het nederlands"),
    "spell":             ("dicts", 0, spell_en, "spell <woord/zin>, spellcheck een woord/zin in het engels"),
    "zauber":            ("dicts", 0, spell_de, "zauber <woord/zin>, spellcheck een woord/zin in het duits"),
    "buchstabieren":     ("dicts", 0, spell_de, ""),
    "schreiben":         ("dicts", 0, spell_de, ""),
    "schreib":           ("dicts", 0, spell_de, ""),
    "watis":             ("dicts", 1000, watis, "watis <iets>, geeft veel bla over <iets>"),
    "wat is ":           ("dicts", 300, wat_is, "wat is <iets>, vertel wat <iets> is"),
    "wat zijn ":         ("dicts", 300, wat_is, ""),
    "dict":              ("dicts", 1000, watis, ""),
    "wiki":              ("dicts", 500, wiki, "wiki <woord> Freeware encyclopedie"),
    "tel":               ("dicts", 1000, tel, "zoek een tel.nr."),

# misc
    "formeer":           ("misc", 100, formeer, "formeer <partijen>, som resultaat van 2e kamer verkiezing 2006"),
    "weer":              ("misc", 100, weer, "weer, zoek het weer op"),
    "zeg":               ("misc", 0, zeg, "zeg <text> [tegen <naam>|op <channel>], ga napraten"),
    "rot":               ("misc", 0, rot_nr, "rot<nr> <text>, versleutel <text> met het rot<nr> algorithme"),
    "dat":               ("misc", 100, last, "dat [x], herhaal wat er x regels terug gezegd werd"),
    "file":              ("misc", 100, filemeldingen, "file <weg>, zoekt fileinformatie op van die weg"),
    "files":             ("misc", 100, filemeldingen, ""),
    "simon?":            ("misc", 100, simon, "simon?, kijkt of simon op sorcsoft ingelogd is"),
    "topic":             ("misc", 100, topic_cmds, "topic <cmd>, doe dingen met de topic"),
    "context":           ("misc", 100, context, "context <text>, geeft de context waarin iets gezegd is"),
    "kies":              ("misc", 100, kies, "kies een willekeurig woord uit de opgegeven lijst"),
    "kookbalans":        ("misc", 100, kookbalans_kookbalans, "geeft een saldolijst"),
    "gekookt":           ("misc", 100, kookbalans_gekookt, "boekt een kookactie"),
    "kookundo":          ("misc", 100, kookbalans_undo, "boekt een inverse kookactie van de laatste kookactie"),
    "vrouwbalans":       ("misc", 100, lambda x: "er zijn hier precies 0 vrouwen", "geeft het aantal vrouwen op het kanaal"),
    "manbalans":         ("misc", 100, lambda x: pietlib.meervoud("er zijn precies 0 mannen, en %d jongen#s hier" % mannen()), "geeft het aantal mannen op het kanaal"),
    "dw":                ("misc", 100, discw, "dw <speler>, bekijkt de inlog status van <speler> op discworld"),
    "dwho":              ("misc", 100, discwho, "dwho, kijk wie van Taido, Irk, Weary of Szwarts op discworld zijn"),
    "gps":               ("misc", 100, gps.gps_coord, "gps <adres> Zoekt GPS coordinaten op van adres"),
    "factor":            ("misc", 100, factor, "factoriseer <nr>"),

# system
    "nmblookup":         ("system", 500, nmblookup, "nmblookup <host>, zoek op campusnet naar een ip"),
    "ping":              ("system", 100, ping, "ping <host>, ping een computer"),
    "geoip":             ("system", 100, geoip, "geoip <ip>, zoekt positie op aarde van ip"),
    "hex":               ("system", 101, hex2dec, "hex <nummer>, reken van/naar hex"),
    "hton":              ("system", 101, hton, "hton[ls] <nummer>, byteswap"),
    "encoding":          ("loos", 1000, test_encoding, "print iso8859 en utf8 karakter"),

# handig
    "remind":            ("handig", 300, remind, "remind <time> <message>, wacht <time> seconden en zeg dan <message>"),
    "was":               ("handig", 300, lambda x: remind("%s %s: je was is weer's klaar" % (x, nick)), ""),
    "reken":             ("handig", 0, lambda x: calc.supercalc(x), "reken uit <expressie> rekent iets uit via de internal piet-processer\nvoor help doe reken help"),
    "calc":              ("handig", 0, lambda x: calc.supercalc(x), ""),
    "temp":              ("handig", 0, temp3, "temp, de temperatuur van sommige plaatsen in de wereld"), 
    "temp2":             ("handig", 0,temp2, "temp, nog een poging om een temperatuur-commando te maken"), 
    "datum":             ("handig", 100, datum, "geef de datum van vandaag"),
    "tijd":              ("handig", 0, commando_tijd, "tijd, geeft aan hoe laat het is in Sydney en Amsterdam"),
    "utc":               ("handig", 100, utc, "utc <secs>|<tijd>, reken van/naar utc"),

# piet
    "changelog":         ("piet", 1000, changelog, "changelog, show the recent changes to piet"),
    "help":              ("piet", 0, command_help, ""),
    "alias":             ("piet", 1000, alias, ""),
    "stop":              ("piet", 1000, leeg, "stop [<reden>], ga van irc"),
    "ga weg":            ("piet", 1000, leeg, "ga weg [van <kanaal>], /leave <kanaal>"),
    "kom bij":           ("piet", 1000, leeg, "kom bij <kanaal>, /join <kanaal>"),
    "kop dicht":         ("piet", 1000, leeg, "kop dicht, hou op met spammen"),
    "auth":              ("piet", -6, change_auth, "auth [<niveau> <nick> [<paswoord>]], geef een authenticatieniveau"),
    "auth iedereen":     ("piet", 1200, auth_iedereen, "auth iedereen, geef iedereen authorisatie 1000 (inclusief jezelf)"),
    "je heet nu":        ("piet", 500, jeheetnu, "je heet nu <nick>, geef nieuwe nick"),
    "renick":            ("piet", 200, randomnaam, "renick, verzint een willekeurige nick"),
    "opme":              ("piet", 500, opme, "opme, geef @"),
    "op me":             ("piet", 500, opme, ""),
    "koffie?":           ("piet", 121, leeg, "koffie?, vraag of ie koffie wil"),
    "wees stil":         ("piet", 1000, leeg, "wees stil, laat piet z'n kop houden met loze dingen"),
    "stil?":             ("piet", 1000, leeg, "stil?, probeert piet zich stil te houden?"),
    "praat maar":        ("piet", 1000, leeg, "praat maar, tegenovergestelde van \"wees stil\""),
    "todo":              ("piet", 1, todo, "todo <text>, voeg wat toe aan de todo list"),
    "bugrep":            ("piet", 1, todo, ""),
    "versie":            ("piet", 100, versie, "versie <x> zoekt laatste versie op van software dinges"),
    "version":           ("piet", 100, versie, ""),
    "mep":               ("piet", 100, mep, ""),
    "geef":              ("piet", 100, geef, ""),
    "tijdzone":          ("piet", 1000, tijdzone, "tijdzone [naam [tijdzone]], verander tijdzones van mensen. zie /usr/share/zoneinfo."),
    "reload":            ("piet", 1000, reloadding, "reload <module> reload iets voor piet"),
    "uptime":            ("piet", 200, uptime, "uptime, verteld tijd sinds eerste python command"),
    "meer":              ("piet", 200, meer, "meer, geef nog's wat meer output van vorig commando"),
    "test":              ("piet", 100, mytest, "ding"),

# geografie / reizen
    "ns":                ("reizen", 100, lambda x: ns.ns(x,channel), "ns van <station> naar <station> via <plaats> vertrek/aankomst <tijd>"),
    "hoever":            ("reizen", 100, lambda x: Distance.Distance(x), "hoever <van> <naar>"),
    "afstand":           ("reizen", 100, lambda x: Distance.Distance(x), ""),
    "distance":          ("reizen", 100, lambda x: Distance.Distance(x), ""),
    "ov":                ("reizen", 200, ov9292_wrapper, "ov \"<van>\" \"<naar>\" vertrek|aankomst datum tijd"),

# stuk
    "doe":               ("stuk", 1200, leeg, "doe <commando>, voer een shell-commando uit"),
    "zoek":              ("stuk", 1000, zoek, "zoek vrouw, zoekt willekeurige vrouw in overijsel"),

# intern
    "onbekend_commando": ("intern", 0, onbekend_commando, "")
};

# we just (re-)read the functions table. (re-)call all piet_init functions in imported modules
for m in [i for i in globals().values() if type(i)==types.ModuleType]:
	if 'piet_init' in m.__dict__:
		m.piet_init(functions)

#param_org: string containing command+parameters
#first: True for outer call, False for recursions
#magzeg: allways True
def parse(param_org, first, magzeg):
  global auth,nick;

  # check of het een calc commando is en voeg dan calc toe voor  het commando
  param_org=calc.addcalc(param_org)

  command = ""
  params = param_org
  for x in functions:
    if param_org.lower().startswith(x) and len(x)>len(command):
      command = x;
      params = param_org[len(command):].strip()

  if params[:2]=="t ":
    params="ik %s helemaal niet, en al zeker niet voor jou" % command
    command="zeg"

  if (command==""):
    if (first):
      command="onbekend_commando";
    else:
      command="zeg";
  
  print (command, params, int(auth));
  
  functie=functions[command];
  if (int(auth)<functie[1]):
    if (first):
      functie=functions["onbekend_commando"];
    else:
      functie=functions["zeg"];
      params=param_org;

  try:
    funcmodule = inspect.getmodule(functie[2])
    if funcmodule:
      funcmodule.channel = channel
      funcmodule.nick = nick
    else:
      print "could not get function module for function"
  except:
    traceback.print_exc();
  
  r="";
  if (int(auth)>=functie[1]):
    if (functie==functions["zeg"]) and not(magzeg):
      r=params;
    else:
      r=functie[2](params);

  if functie[0] == "stuk":
    piet.send(channel, "pas op, deze functie werkt niet helemaal zoals bedoeld")
  meer_data[nick]=[]
  maxlines=10
  if type(r) == type(None):
    return "rare functie, kwam niks uit"
  r2=[i for i in r.split('\n') if len(string.strip(i))>0]
  if len(r2) > maxlines+1:
    l=str(len(r2));
    meer_data[nick]=r2[maxlines:];
    r=string.join(r2[:maxlines], '\n')+\
      ('\n%s: %d van de %d regels vind ik zat, maar "meer" geeft meer\n' %
      (nick, int(maxlines), int(l)));
  return r;

prev_command="niets";

def do_command(nick_, auth_, channel_, msg_):
  global nick,auth,channel,prev_command;
  nick=nick_;
  auth=int(auth_);
  channel=channel_;
  if (msg_[0:2]=="s/"):
    regexparts=string.split(msg_,"/");
    if (len(regexparts)==3) or (len(regexparts)==4):
      if (prev_command=="niets"):
        piet.send(channel_, "geen vorig commando, wat wil je nou?\n");
        return;
      msg_=re.sub(regexparts[1], regexparts[2], prev_command);

  prev_command=msg_;
  print "executing nick=%s, auth=%s, channel=%s, msg=%s" % (repr(nick), repr(auth), repr(channel), repr(msg_))
  try:
    result=parse(msg_, True, True);
    if type(result) == unicode:
      result = result.encode('UTF-8')
    piet.send(channel_, result);
  except pietlib.piet_exception, e:
    piet.send(channel_, str(e))


