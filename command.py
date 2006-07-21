#!/usr/bin/python
# -*- coding: iso-8859-1 -*-

import sys,string,random,re,os,time,crypt,socket,thread,urllib,traceback,datetime;
import piet;
from telnetlib import Telnet;
sys.path.append(".");
from calc import addcalc;
from calc import supercalc;
import Distance;
import BeautifulSoup;
from pistes import cmd_pistes;
import pietlib;
from bash import bash;

todofile = "todo.txt";
logfile = "log.txt";

nick = "";#string.strip(sys.stdin.readline());
auth = -5;#int(string.strip(sys.stdin.readline()));
channel = "";#string.strip(sys.stdin.readline());
d={};
meer_data={};

try:
	nicks;
except:
	nicks={};

def db_get(table, keycol, key, valuecol):
	try:
		result=piet.db("SELECT "+valuecol+" FROM "+table+" WHERE "+keycol+"=\""+key+"\"");
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
	result=time.strftime("Het is nu %d-%m-%Y (in de tijdzone "+tz.lower()+")", time.localtime());
	pietlib.timezone_reset();
	return result;

def error_handler(type, value, tb):
	global channel;
	traceback.print_exc();
	piet.send(channel, "arg! er heeft weer iemand zitten prutsen! wie is't? ik moet even "+repr(value.args[0])+" op z'n voorhoofd tatoeëren\n");
	sys.__excepthook__(type, value, tb);

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
	if (len(split)>=2) and len([1 for x in split[1:] if x in nicks])==len(split)-1:
		return emote(split[0],split[1:]);

	if (len(param)==0):
		return "ok\n";
	elif (param[-1]=='?'):
		if (random.random()>=0.475):
			return "ja\n";
		else:
			return "nee\n";
	elif param in groeten:
		return random.choice(groeten)+"\n";
	elif param in ["stfu"]:
		return "jaja, ik zeur\n";
	return "oh\n";

def emote(action, nicks):
	if len(action)==0 or len(nicks)==0:
		return "ACTION frot";
	if len(nicks)==1 and nicks[0]==piet.nick():
		nicks=[nick];
	toevoeging=["met tegenzin", "dan maar even", "met een diepe zucht", \
						 "enthousiast", "zonder genade", "alsof z'n leven ervan afhangt",\
						 "nauwelijks", "bijna, maar toch maar niet", "vol overgave"];
	if action[-1] in "aeoui":
		action=action+action[-1];
	if action[-1]!='t':
		action=action+"t";
	return "ACTION "+action+" "+pietlib.make_list(nicks)+" "+random.choice(toevoeging);



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
			if (len(away)>0): msg=msg+" "+away+" ken ik ook nog, maar die zijn hier niet";
			return msg;
		except:
			traceback.print_exc();
			return "ik heb geen idee, zoek het lekker zelf uit";

	newauth=0; parnick="";
	try:
		newauth=int(par[0]);
		parnick=par[1];
	except:
		newauth=int(par[1]);
		parnick=par[0];
	if (newauth>1500): newauth=1500;
	if (newauth<-1500): newauth=-1500;

	passok=False;
	if (parcount==3):
		encrypted=crypt.crypt(par[2], "AB");
		print "AUTH: encrypted ww = \""+encrypted+"\"\n";
		if (encrypted=="ABVBPZGw0mmyg"):
			localauth=max(localauth, 1000); # user can give authorization as-if his authorisation was 1000
		else:
			return "achja, leuk geprobeerd, niet goed helaas..\n";

	try:
		oldauth=int(piet.db("SELECT auth FROM auth WHERE name=\""+parnick+"\"")[1][0]);
	except:
		oldauth=-5;

	oldauth=int(db_get("auth", "name", parnick, "auth") or -5);
	if (newauth>localauth):
		return "je hebt maar "+str(localauth)+" auth, dus meer mag je niet geven";
	if (localauth<=oldauth and parnick!=nick):
		return "en wie ben jij dan wel, dat je zomaar denkt "+parnick+" authorisatie te kunnen geven?!?";
	if (newauth<=localauth and localauth>=oldauth):
		oldtz=db_get("auth", "name", parnick, "timezone");
		if (oldtz):
			piet.db("REPLACE INTO auth(name,auth,timezone) VALUES(\""+\
					parnick+"\","+str(newauth)+",\""+oldtz+"\")");
		else:
			piet.db("REPLACE INTO auth(name,auth) VALUES(\""+parnick+"\","+str(newauth)+")");
		# check_names(nick_, channel_, msg_), would be nice, strange library dependancy though
		return "ok, "+parnick+" heeft nu authenticatieniveau "+str(newauth)+"\n";
	return "bogus"; # never reached, i think


try:
  boottime;
except:
  boottime=time.time();

def hex2dec(params):
	if (params[:2]=="0x" or params[-1]=='h'):
		if (params[-1]=='h'): params=params[:-1];
		if (params[:2]=='0x'): params=params[2:];
		try:
			val=int(params, 16);
		except:
			traceback.print_exc();
			return "doe nou niet alsof dat hexadecimaal is.. dat is't niet";
		result="0x"+params+" wordt door sommigen aangeduid als "+str(val);
		if (val>=2**7 and val<=2**8):
			result+=", en soms ook als -"+str(2**8-val);
		elif (val>=2**15 and val<=2**16):
			result+=", en soms ook als -"+str(2**16-val);
		elif (val>=2**31 and val<=2**32):
			result+=", en soms ook als -"+str(2**32-val);
		elif (val>=2**63 and val<=2**64):
			result+=", en soms ook als -"+str(2**64-val);
		return result;
	try:
		print "converting \""+params+"\""
		val=int(params);
	except:
		traceback.print_exc();
		return "ACTION stuurt een grote boze heks op je af";
	if (val>=0):
		return str(val)+" is ook wel "+hex(val);
	if (val>=-(2**7)):
		return str(val)+" is dus "+hex(2**8+val);
	elif (val>=-(2**15)):
		return str(val)+" is dus "+hex(2**16+val);
	elif (val>=-(2**31)):
		return str(val)+" is dus "+hex(2**32+val);
	elif (val>=-(2**63)):
		return str(val)+" is dus "+hex(2**64+val);
	else:
		return str(val)+" is wel heel klein, "+hex(val);
	
		
	
def uptime(params):
	ut=time.time()-boottime;
	minutes,seconds=int(ut/60),int(ut%60);
	hours,minutes=int(minutes/60),int(minutes%60);
	days,hours=int(hours/24),int(hours%24);
	if (days>100):
		return "ben oud... "+str(days)+" dagen (en "+str(hours)+" uur)"
	elif (days>31):
		return "ben met "+str(days)+" dagen en "+str(hours)+" toch een goede irc verslaafde"
	elif (days>1):
		return "woei! alweer "+str(days)+" dagen (en "+str(hours)+" uur en "+str(minutes)+" minuten)";
	elif (days>0):
		return "toch alweer een dag en "+str(hours)+" uur (en "+str(minutes)+" minuten)";
	elif (hours>1):
		return "alweer "+str(hours)+" uur en "+str(minutes)+" minuten";
	elif (hours>0):
		return "een uurtje, en "+str(minutes)+" minuten";
	else:
		return str(minutes)+" minuten en "+str(seconds)+" secs";


def kies(params):
  if string.find(params,"\"") >= 0:
    list=[]
    while params!="":
      if params[:1]=="\"":
        i=string.find(params,"\"",1)
        if i<0:
          return "probleem met \""
        else:
          list+=[params[1:i]]
          while params[i+1:i+2]==" ":
            i+=1
          params=params[i+1:]
      else:
        i=string.find(params," ",1)
        if i<0:
          i=len(params)
        list+=[params[:i]]
        while params[i:i+1]==" ":
          i+=1
        params=params[i:]     
  else:
    list=string.split(params," ")
  choice=random.choice(list);
  choice=string.strip(parse(choice, False, True));
  return choice



def vandale(woord):
  comm="lynx -dump -width 600 http://www.vandale.nl/opzoeken/woordenboek/?zoekwoord="+woord+" | grep -A 5000 maximaal\ 20\ woorden | grep -B 5000 verfijnd\ zoeken | grep -v maximaal\ 20\ woorden | grep -v verfijnd\ zoeken";
  comm=comm+" | grep -v gif]";
  inp = os.popen(comm);
  result=inp.read();
  if (re.search("Unable to connect", result)!=None):
    return "vandale stuk, echt\n";
  else:
    result=string.split(result, '\n');
    result=[re.sub("\267", ".", string.strip(i)) for i in result];
    result=["  "+re.sub("\264", "\'", i) for i in result if (i<>"")];
    result=string.join(result, '\n');
    if (len(result)>0):
      return result+"\n";
    else:
      return "helaas niet gevonden\n";

def rijm(woord):
	try:
		input=pietlib.get_url("http://www.rijmwoorden.nl/rijm.pl?woord="+string.strip(woord));
	except:
		return "ik kan niet rijmen zonder de website, dus je zult 't zelf moeten doen";
	soup=BeautifulSoup.BeautifulSoup(input);
	woorden=[x.string for x in soup.table("td") if x.string!=BeautifulSoup.Null];
	if (len(woorden)==0):
		return "daar rijmt echt helemaal niks op";
	return "oh, dat is makkelijk: "+string.join(woorden, ', ');

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
	x='<?xml'+string.split(fs.read(), '<?xml')[1]; # read only the part after <?xml

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

def SydWeer(woord):
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
  if (string.lower(woord)=="sydney") or  (string.lower(woord)=="syd"):
     return SydWeer("");
  if (string.lower(nick)[:6]=="semyon") and (string.lower(woord)!="nl"):
     return SydWeer("");
  #cmd = "lynx -dump http://teletekst.nos.nl/cgi-bin/tt/nos/page/t/703";
  cmd = "lynx -dump http://www.weer.nl/indexnew.phtml"
  inp,outp,stderr = os.popen3(cmd);
  result=outp.read();
  inp.close();
  outp.close();
  stderr.close();
  i=string.find(result,"]weerkaart")+11;
  j=string.find(result,"[",i);
  lines=string.split(string.strip(result[i:j]),'\n');
  result="";
  for str in lines:
    result+=string.strip(str)+" ";  
    if len(str)<2:
      result+='\n';
  return string.strip(result);

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
	return "'"+woord+"' ken ik niet hoor, hier is het nederlandse weer:\n"+nlweer("");


try:
	zeghisttijd;
	zeghistnicks;
except:
	zeghisttijd=0;
	zeghistnicks=[];

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
		piet.send(kanaal, "zo, dat heb ik even goed gezegd, niet dan "+pietlib.make_list(n)+"?");
	return "";

def rot_nr(cmd):
	n,y=string.split(cmd, " ", 1);
	n=int(n)%26;
	y=string.strip(parse(y, False, True));
	return "".join([x.isalpha() and (ord(x.lower())-ord("a")>=26-n and chr(ord(x)+n-26) or chr(ord(x)+n)) or x for x in y])

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

def afk(woord):
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
		if len(result)<12:
			s=string.join(result, '\n');
			if len(rest)>0:
				s=s+'\n'+pietlib.make_list(rest);
		else:
			s=pietlib.make_list(result); # ignore rest, we already have a lot
	
	return s;

def afk_source2(woord):
	try:
		a=pietlib.get_url_soup("http://www.afkorting.net/cgi-local/s.pl?pg=a&s="+woord);
		r=a.table.findAll("tr", recursive=False);
		r=[i.findAll("td") for i in r];
		r=[conf(i[1].contents[0]) for i in r if len(i)>=2];
		return r;
	except:
		traceback.print_exc();
		piet.send(channel, "helaas, afkortingen.net wilde me niet te woord staan\n");
	return [];

# input: searchword
# output: list of possible meanings
def afk_source3(woord):
	try:
		a=pietlib.get_url_soup("http://acronyms.thefreedictionary.com/"+woord, "bla/bla");
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
		piet.send(channel, "helaas, de afkortingen die ik uit m'n hoofd ken zijn zoek\n");
	return [];

def changelog(dinges):
  command="darcs cha --last=5 | sed -e '/^$/d;N;s/\\n//g;s/<[a-zA-Z]\\+@[a-zA-Z\\.]\\+>//;s/[\\t\\ ]\\+/ /g'";
  inp = os.popen(command);
  result=inp.read();
  inp.close();
  return "echt veel is er niet veranderd...\n"+result;

def spell_int(woorden, lang):
  outp, inp = os.popen2("aspell -a --lang="+lang);
  outp.write(woorden);
  outp.close();
  result=string.split(inp.read(), '\n');
  result=[re.sub("& (\w+) \d+ \d+:", "\\1: ", i) for i in result[1:] if (i<>"*") and (i<>"")];
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


def random_sentence(woorden):
	try:
		s=pietlib.get_url_soup("http://watchout4snakes.com/creativitytools/RandomSentence/RandomSentence.aspx");
		l=s.findAll("span", {"class":"randomSentence"})[0].contents[0];
		return l.encode();
	except:
		traceback.print_exc();
		return "'t is stuk, nu geen zin";

def help(param):
  global d,auth;
  try:
    return d[param][2]+"\n";
  except:
    r=[b for b in d if (d[b][2]<>"") and (d[b][0]<=auth)];
    r.sort();
    return string.join(r, ', ')+"\n";

def alias(param):
  global d,auth;
  r=[b for b in d if (d[b][2]=="") and (d[b][0]<=auth)];
  r.sort();
  return string.join(r, ', ')+"\n";

def spreuk(param):
  inf = open("ol.txt");
  lines = string.split(inf.read(), '\n');
  inf.close();
  return random.choice(lines)+"\n";

def ping(woord):
  a=string.split(woord, ' ');
  if (len(a)<>1) or (len(a[0])==0):
    return nick+": pong\n";
  else:
    inp = os.popen("ping -q -c 10 "+a[0]+" | tail -n 2");
    result=inp.read();
    return result+"\n";

def zoek(param):
	if (param=="vrouw"):
		return zoekvrouw(param);
	return 'alleen "zoek vrouw" werkt'

def zoekvrouw(param):
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
  a=string.split(regel, ' ');
  if (len(a)<1):
    return "brontaal mist\n";
  else:
    bron="X";
    a[0] = string.lower(a[0]);
    if ((a[0] == "nl") or (a[0] == "dutch") or (a[0] == "nederlands") or (a[0] == "ne")):
      bron="Dutch";
    if ((a[0] == "en") or (a[0] == "english") or (a[0] == "engels") or (a[0] == "eng")):
      bron="English";
    if ((a[0] == "sp") or (a[0] == "spanish") or (a[0] == "spaans") or (a[0] == "spa")):
      bron="Spanish";
    if ((a[0] == "du") or (a[0] == "german") or (a[0] == "dl") or (a[0] == "duits") or (a[0] == "dui") or (a[0] == "ge")):
      bron="German";
    if (bron == "X"):
      return "sorry, ik spreek geen "+a[0]+" "+"\n";
  if (len(a)<2):
    return "doeltaal mist\n";
  else:
    doel="X";
    a[1] = string.lower(a[1]);
    if ((a[1] == "nl") or (a[1] == "dutch") or (a[1] == "nederlands") or (a[1] == "ne")):
      doel="Dutch";
    if ((a[1] == "en") or (a[1] == "english") or (a[1] == "engels") or (a[1] == "eng")):
      doel="English";
    if ((a[1] == "sp") or (a[1] == "spanish") or (a[1] == "spaans") or (a[1] == "spa")):
      doel="Spanish";
    if ((a[1] == "du") or (a[1] == "german") or (a[1] == "dl") or (a[1] == "duits") or (a[1] == "dui") or (a[1] == "ge")):
      doel="German";
    if (doel == "X"):
      return "sorry, ik spreek geen "+a[1]+"\n";
  if (doel==bron):
    return "ja zeg, dat heet geen vertalen meer, met dezelfde talen\n";
  if (len(a)<3):
    return "niks te vertalen, verveel me\n";
  regel=string.strip(string.join(a[2:]," "));
  regel=string.strip(parse(regel, False, True));
  regel=string.split(regel," ");
  regel=string.join(regel,"%20");
  i1 = string.find(regel,".");
  while i1 > 0:
    regel = regel[:i1]+".%20"+regel[i1+1:];
    i1 = string.find(regel,".",i1+3);
  i2 = string.find(regel,",");
  while i2 > 0:
    regel = regel[:i2]+",%20"+regel[i2+1:];
    i2 = string.find(regel,",",i2+3);

  if (len(string.split(regel,"%20"))==1):
  # voor een enkel woord gebruiken we intertran... die geeft
  # namelijk voor een woord meerdere opties... voor meer worden gebruiken
  # we liever babelfish
  # Intertran:

    c = "wget -O - -q";
    c = c+" \"http://www.tranexp.com:2000/Translate/result.shtml?text=";
    c = c+regel+"&from="+bron+"&to="+doel+"\"";
    outp = os.popen(c);
    result = outp.read();
    i1 = string.rfind(result,"<textarea");
    i2 = string.rfind(result,"/textarea");
    result=result[i1:i2];
    i1 = string.find(result,">");
    i1=i1+1;
    i2 = string.rfind(result,"<");
    result=result[i1:i2];
    result=string.strip(result);	
  else:
  # babelfish:
    Command = "wget -O - -q ";
    Command = Command + "\"http://world.altavista.com/babelfish/tr?urltext=";
    Command = Command + regel+"&lp=";
    if (bron=="Dutch"):
      Command = Command + "nl_";
    elif (bron=="German"):
      Command = Command + "de_";
    elif (bron=="Spanish"):
      Command = Command + "es_";
    elif (bron=="English"):
      Command = Command + "en";
    if (doel=="Dutch"):
      Command = Command + "nl";
    elif (doel=="German"):
      Command = Command + "de";
    elif (doel=="Spanish"):
      Command = Command + "es";
    elif (doel=="English"):
      Command = Command + "en";
    Command = Command + "\"";
    outp = os.popen(Command);
    result = outp.read();
    i1 = string.find(result,"<td bgcolor=white");
    i1 = string.find(result,"<div",i1);
    i1 = string.find(result,">",i1);
    i2 = string.find(result,"</div",i1);
    result=result[i1:i2+1];
    i1 = string.find(result,">");
    i1=i1+1;
    i2 = string.rfind(result,"<");
    result=result[i1:i2];
    result=string.strip(result);
    i1=string.find(result,"&#39;");
    while (i1>=0):
      result=result[0:i1]+"'"+result[i1+5:];
      i1=string.find(result,"&#39;");
    i1=string.find(result,"&#9;");
    while (i1>=0):
      result=result[0:i1]+"'"+result[i1+4:];
      i1=string.find(result,"&#9;");
    result=string.split(result,'\n');
    result=string.join(result," ");

  if (result=="") :
    d={"Spanish": "Spaans",
       "German": "Duits",
       "Dutch": "Nederlands",
       "English": "Engels"};
    doel=d[doel];
    result="wuh, nu even niet vertalen naar "+doel+" hoor, probeer het nog eens.";
  return result;

def dvorak2qwerty(params):
  params = string.strip(parse(params, False, True));
  outp,inp = os.popen2("tr \"anihdyujgcvpmlsrxo;kf.,bt/weqANIHDYUJGCVPMLSRXO:KF><BT?WEQ\" \"abcdefghijklmnopqrstuvwxyz,.'ABCDEFGHIJKLMNOPQRSTUVQXYZ<>\\\"\"");
  outp.write(params);
  outp.close();
  result=inp.read();
  return(result);

def last(params):
  params = string.strip(params);
  try:
    line=int(params);
  except:
    line=1;
  inp = os.popen("tail -n "+str(line)+" log.txt | head -n 1");
  result=inp.read();
  return(result);

def leet(params):
  params = string.strip(parse(params, False, True));
  outp,inp = os.popen2("tr \"eilatbosgEILATBOSG\" \"311478059311478059\"");
  outp.write(params);
  outp.close();
  result=inp.read();
  return(result);
  
  
def unleet(params):
  params = string.strip(parse(params, False, True));
  outp,inp = os.popen2("tr \"311478059\" \"eilatbosg\"");
  outp.write(params);
  outp.close();
  result=inp.read();
  return(result);

def todo(params):
  if (params==""):
    inf = open(todofile);
    lines = [a for a in string.split(inf.read(), '\n') if a<>""];
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

def url(params):
	cmd="sed -n '/http\|www/{s/.*\(http\|www\)/\\1/;T;s/[[:blank:]].*//;p}' log.txt"
	inp = os.popen(cmd);
	result = string.split(inp.read(), '\n');
	inp.close();
	result = random.choice(result);
	return result;

def news(params):
	cmd="lynx -dump -width=500 http://podium.trouw.nl/novum/laatstenieuws.rss";
	cmd+="|awk '{ result=result $0 } END { print result }' | sed 's/<\\/item>/<\\/item>\\n/g'" # get one item per line
	cmd+="| sed -n 's/^.*<item>\(.*\)<\\/item>.*/\\1/;T;p'" # only the items
	if (len(params)<1):
		cmd+="| sed 's/.*<title>\(.*\)<\\/title>.*/\\1/'" # get the title
	elif ((params=="-v") or (params=="verbose") or (params[0:4]=="uitg")):
		cmd+="| sed 's/.*<title>\(.*\)<\\/title>.*";
		cmd+="<description>\(.*\)<\\/description>.*/\\1\\n\\2\\n-/'"; # get the title+description
	else:
		cmd+="| grep '"+params+"'"; # only the requested items
		cmd+="| sed 's/.*<description>\(.*\)<\\/description>.*/\\1/'" # get the description
	inp = os.popen(cmd);
	result = string.split(inp.read(), '\n');
	if (len(result)<2):
		result+="niks";
	return string.join(result, '\n');

def simon(params):
  cmd="w | grep simon | head -1 | wc -l | sed -e \"s/.*1.*/ja,\ een\ simon/;s/.*0.*/nee,\ nog\ niet/\"";
  inp = os.popen(cmd);
  result=string.strip(inp.read());
  return(result);

def galgje(regel):
  a=string.split(regel, ' ');
  if (len(a)<0):
    return "doe eens galgje start ofzo\n";
  else:
    i1 = string.lower(string.strip(a[0]));
    if (i1 == "start"):
      gf = open("list.txt");
      lines = [a for a in string.split(gf.read(), '\n') if a<>""];
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
        lines = [i for i in string.split(tempf.read(), '\n') if i<>""];
        blind=lines[0];
        index=lines[1];
        times=string.atoi(lines[2]);
        gehad=lines[3];
        tempf.close();
        gf = open("list.txt");
        lines = [i for i in string.split(gf.read(), '\n') if i<>""];
        gf.close();
        word=string.lower(lines[string.atoi(index)]);
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

def citaat(regel):
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
      result="oei, iets mis met nmblookup, ik kreeg \""+string.join(lines, ' ')+"\"\n";
    return(result);

def sin(regel):
  return(nmblookup("sin"));
  
def context(regel):
  cmd="cat log.txt | grep -B2 -A2 \""+regel+"\"";
  inp = os.popen(cmd);
  result=inp.read();
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
    tn = Telnet('discworld.imaginary.com', 4242);
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
   
def discwho(regel):
  tn = Telnet('discworld.imaginary.com', 4242);
  tn.write("u\nq\n");
  outp=tn.read_until("Press enter to continue");
  tn.close();
  outp=string.lower(outp);
  result="";
  if (string.find(outp,"irk")>0):
    result+="irk, ";
  if (string.find(outp,"szwarts")>0):
    result+="szwarts, ";
  if (string.find(outp,"taido")>0):
    result+="taido, ";
  if (string.find(outp,"quences")>0):
    result+="quences, ";
  if (len(result)<=0):
    return "niemand!";
  return result[:len(result)-2];

def geordi(input):
  A=random.choice(("perform a level E diagnostic on", "run a level E diagnostic on","reroute the B C D to","redirect the B C D to","divert the B C D to","bypass","amplify","modify","polarize","reconfigure","extend","rebuild","vary","analyze","adjust","recalibrate"));
  A="we need to "+A+" the B C D!";
  while (string.find(A,"B")>0):
    B=random.choice(("field","tachyon","baryon","lepton","e-m","phase","pulse","sub-space","spectral","antimatter","plasma","bandwidth","particle"));
    A=A[0:string.find(A,"B")]+B+A[string.find(A,"B")+1:];
  while (string.find(A,"C")>0):
    C=random.choice(("dispersion","induction","frequency","resonance"));
    A=A[0:string.find(A,"C")]+C+A[string.find(A,"C")+1:];
  while (string.find(A,"D")>0):
    D=random.choice(("conduit","discriminator","modulator","transducer","wave-guide","coils","matrix","sensors","invertor"));
    A=A[0:string.find(A,"D")]+D+A[string.find(A,"D")+1:];
  while (string.find(A,"E")>0):
    E=random.choice(("one","two","three","four","five"));
    A=A[0:string.find(A,"E")]+E+A[string.find(A,"E")+1:];
  line="Captain, "+A;
  return line;

def jeheetnu(input):
	while (len(input)<4):
		input=input+"-";
	return "NICK "+input;

def randomnaam(input):
  getdiscworldname=(random.random() > 0.5);
  if (getdiscworldname):
    try:
      getdiscworldname=(discwho("")=="niemand!")
    except:
      getdiscworldname=(1==0);
  if (getdiscworldname):
    #discworld name
    tn = Telnet('discworld.imaginary.com', 4242);
    tn.read_until("Your choice:");
    tn.write("n\n");
    tn.read_until("'g' for a list");
    tn.read_until("generated names:");
    tn.write("g\n");
    result=tn.read_until("Your choice?");
    result=string.split(result, '\n');
    categorynum=random.randint(1,8);
    category=result[categorynum+1][4:];
    n=string.find(category, "(");
    if (n!=-1):
      category=string.strip(category[:n-1]);
  
    tn.write(string.digits[categorynum]);
    tn.write("\n");
    result=tn.read_until("Your choice?");
    tn.close();
    result=string.split(result, '\n');
    naam=string.strip(result[random.randint(1,9)][4:]);
    #print("\nnaam \""+naam+"\" uit category \""+category+"\"\n");
  else:
    #http://www.ruf.rice.edu/~pound/ naam
    cmd="wget -q -O - http://www.ruf.rice.edu/~pound | grep \"<li><a\" | grep \"sample out\"";
    inp,outp,stderr = os.popen3(cmd);
    result = outp.read();
    outp.close();
    inp.close();
    stderr.close();
    result = string.split(result,'\n');
    line = random.choice(result);
    i1 = string.rfind(line,"=\"");
    i2 = string.rfind(line,"\">");
    url = "http://www.ruf.rice.edu/~pound/"+line[i1+2:i2];
    i1 = string.find(line,"\">");
    i2 = string.find(line,"</a>");
    category=line[i1+2:i2];
    cmd = "wget -q -O - "+url;
    inp,outp,stderr = os.popen3(cmd);
    result = outp.read();
    outp.close();
    inp.close();   
    stderr.close();
    result = string.split(result,'\n');
    naam=random.choice(result);
  return "NICK "+naam+"\nik heb deze keer gekozen voor een naam uit de categorie \""+category+"\"\n";

try:
	remind_threads;
except:
	remind_threads=0;
def remind_thread(channel, frop):
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
				tijd=min(next, int(float(piet.db("SELECT MIN(tijd) from reminds")[1][0])));
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
					telaat=now-int(float(m[3]));
					if (telaat>0):
						piet.send(m[0], m[2]+" (ja, "+pietlib.format_tijdsduur(telaat)+" te laat)");
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
			return list_reminds(string.strip(regel[5:]));
	except:
		traceback.print_exc();
		return "frop";
	relformat="((\d+\s*(j|jaar|jaren|w|week|weken|d|dagen|dag|uren|uur|u|h|min|m|s|sec)\s*)+)\W";
	absformat="(("+pietlib.dateregex+"\s+)?\d+:\d+[:\d+]\s*)";
	split=re.match("\s*("+absformat+"|"+relformat+")", regel); #abs voor rel, want 1m en 1maart lijken op elkaar
	if (split==None):
		return "zou je dat nog eens helder kunnen formuleren? ik snap er niks van";
	now=int(round(time.time()));
	tijd=string.strip(split.group(0));
	result = string.strip(regel[split.end():]);
	if (len(result)==0):
		result=nick+": ik moest je ergens aan herinneren, maar zou niet meer weten wat";
	tz=pietlib.tijdzone_nick(nick);
	if (string.find(tijd, ":")==-1): # relative time if no :
		tijd=re.sub(" ", "", tijd);
		tijd=string.replace(tijd, "jaren", "j");
		tijd=string.replace(tijd, "jaar", "j");
		tijd=string.replace(tijd, "weken", "w");
		tijd=string.replace(tijd, "week", "w");
		tijd=string.replace(tijd, "dagen", "d");
		tijd=string.replace(tijd, "dag", "d");
		tijd=string.replace(tijd, "uren", "h");
		tijd=string.replace(tijd, "uur", "h");
		tijd=string.replace(tijd, "u", "h");
		tijd=string.replace(tijd, "min", "m");
		tijd=string.replace(tijd, "sec", "s");
		tijd=string.replace(tijd, "m", "*60 ");
		tijd=string.replace(tijd, "h", "*3600 ");
		tijd=string.replace(tijd, "d", "*24*3600 ");
		tijd=string.replace(tijd, "w", "*7*24*3600 ");
		tijd=string.replace(tijd, "j", "*365*24*3600 ");
		tijd=string.replace(tijd, "s", " ");
		tijd=string.strip(tijd);
		tijd=re.sub('\ +', '+', tijd);
		tijd=eval(tijd); # tijd in secs t.o.v now
		if (tijd < 0):
			return "tijdsaanduiding klopt niet";
		elif (tijd == 0):
			return "dat is nu. je bent wel erg vergeetachtig, niet?";
		tijdstr=pietlib.format_localtijd(now+tijd, tz);
		piet.send(channel, "ok, ergens rond "+tijdstr+" zal ik dat wel's roepen dan, als ik zin heb\n");
	else: # absolute time
		try:
			tijd=pietlib.parse_tijd(tijd, tz)-time.time();
		except:
			return "volgens mij hou je me voor de gek, wat is dit voor rare tijd?";
		if (tijd<120):
			piet.send(channel, "dat is al over "+str(tijd)+" seconden! maar goed, ik zal herinneren\n");
		else:
			piet.send(channel, "goed, ik zal je waarschuwen. maar pas over "+pietlib.format_tijdsduur(tijd)+", hoor\n");
	if (tijd<5*60 and tijd>=0):
		chan=channel;
		time.sleep(tijd);
		piet.send(chan, string.strip(parse(result, False, True)));
		return "";
	# meer dan 5 min, stop in db
	# CREATE TABLE reminds (channel string, nick string, msg string, tijd int)
	piet.db("INSERT INTO reminds VALUES(\""+
			string.replace(channel, '"', '""')+"\",\""+
			string.replace(nick, '"', '""')+"\",\""+
			string.replace(result, '"', '""')+"\","+
			repr(now+tijd)+");");
	piet.thread(channel, "remind_thread", ""); # make sure a thread is running
	return "";
piet.thread(channel, "remind_thread", "");

def list_reminds(regel):
	try:
		qry="SELECT channel,nick,msg,tijd FROM reminds";
		if (regel!="all"):
			qry+=" WHERE nick=\""+nick+"\"";
		qry+=" ORDER BY tijd";
		try:
			msgs=piet.db(qry)[1:];
		except:
			return "ik herinner je helemaal nergens aan..";

		now=int(round(time.time()));
		#[piet.send("weary", repr(int(round(float(x[3])))-now)) for x in msgs if len(x)==4];
		msgs=["over "+pietlib.format_tijdsduur(int(round(float(x[3])))-now)+", \""+x[2]+"\"" for x in msgs if len(x)==4]; # pak tijd
		piet.send(channel, string.join(msgs, '\n'));

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
  if (params[0]=="piet" or params[0]=="jezelf" or params[0]=="zichzelf"):
    return "ACTION heeft een hekel aan zichzelf, maar doet niet aan zelfverminking";
  r=random.random();
  if (r<=0.1):
    return "ik zou niet weten waarom";
  if (r<=0.2):
    return "ACTION mept "+nick+" zelf";
  if (r<=0.5):
    return "ACTION deelt een corrigerende mep uit aan "+params[0];
  return "ACTION mept "+params[0];

def geef(regel):
  params=string.split(regel,' ');
  if (len(params)<1) or (len(params[0])==0):
    return "ACTION geeft "+nick+" een blik van verstandhouding";
  i=0;
  before="";
  line="";
  for a in params:
    before+=a+" ";
    if a=="aan":
      line=before;
  if (line!=""):
    return "ACTION geeft "+before;
  return "ACTION deelt "+params[0]+" "+string.join(params[1:],' ')+" uit";

def dum(regel):
  r=random.random();
  if (r<=0.2):
    return "die dum dum";
  if (r<=0.5):
    print "piet: verklaar dum"
    return verklaar("dum");
  return "dat jij je verveelt is ok, maar dan hoef je mij nog niet er mee te vermoeien";

def docommand(cmd):
  inp,outp = os.popen2(cmd);
  result = string.split(outp.read(), '\n');
  outp.close();
  inp.close();
  return result;


def tempwereld(regel):
  regel=string.lower(regel)
  regel=string.replace(regel,"new york","new_york");
  regel=string.replace(regel,"den haag","den_haag");
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
    elif (City=="l'sum" or City=="loppersum"):
      City="Loppersum";
    elif (City=="g'ing" or City=="groningen" or  City=="grunnen" or City=="g'ningen"):
      City="Groningen";
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
    elif (City=="p'burgh" or City=="pennsylvania" or City=="pittsburgh"):
       City="Pittsburgh";
    url="";

    cityurlmap=[("Enschede","?ID=IOVERIJS5","CET"),("Loppersum","?ID=IGRONING8","CET"),("New York","?ID=KNYNEWYO17","EST"),("Groningen","?ID=IGRONING9","CET"),("Leeuwarden","?ID=IFRIESLA16","CET"),("Sydney","?ID=INSWWEST1","AEST"),("Pittsburgh","?ID=KPAPITTS8","EDT"),("Hilversum","?ID=IHILVERS3","CET"),("Rotterdam","?ID=IZHROTTE2","CET"),("Amsterdam","?ID=INOORDHO1","CET"),("Cairns","?ID=IQUEENSL32","AEST"),("Johannesburg","?ID=IGAUTENG8","SAST"),("Den Haag","?ID=IZUIDHOL11","CET")];
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
	if (plaats=="h'sum") or (plaats=="hilversum"):
		plaats="de bilt";
	elif (plaats=="r'dam"):
		plaats="rotterdam";
	elif (plaats=="e'de") or (plaats=="enschede") or (plaats=="twente"):
		plaats="twenthe";
	elif (plaats=="a'dam") or (plaats=="amsterdam") or (plaats=="diemen") or (plaats=="dmz"):
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
	
	line="op "+string.join(result[0][1:], ' ')+" in "+string.lower(myline[0])+": ";
	line+=string.join(myline[1:][:-6])+" en "+myline[-6]+" graden. ";
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
  cmd = "lynx -dump http://nl.wikipedia.org/w/wiki.phtml?search="+regel+"  | grep -A 20 Overeenkomst\ met\ v | grep -B 20 Overeenkomst\ met\ a | grep \"bytes)\"";
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
        if (string.lower(string.join(string.split(string.strip(a[0]),' '),"%20"))==string.lower(regel)):
          newurl="http://nl.wikipedia.org/wiki/"+string.replace(string.strip(a[0]),' ','_');
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

def tijd(regel):
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
		if (oldauth==None or len(oldauth)<2):
			piet.db('REPLACE INTO auth(name,timezone) VALUES("'+a[0]+'","'+tijdzone+'")');
		else:
			piet.db('REPLACE INTO auth(name,auth,timezone) VALUES("'+a[0]+'",'+\
				oldauth[1][0]+',"'+tijdzone+'")');

		if tijdzone==a[1]:
			return "zozo, jij kent je tijdzones goed. ik zet "+a[0]+" in "+tijdzone+"\n";
		else:
			return "ik zet "+a[0]+" wel in "+tijdzone+", dat lijkt wel wat op "+a[1]+"\n";
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
    inf.close;
    lines=lines+regel+"\n";
    outf=open("quote.txt","w");
    outf.write(lines);
    outf.close;
    return "toegevoegt: \""+regel+"\"";
  return "Syntax is fout voor quote";

def tv_nuenstraks(regel):
	soup=pietlib.get_url_soup("http://www.tvgids.nl/nustraks/");
	t=soup('div', {'id' : 'nuStraks'})[0].div.form.table;
	needed=set(["Nederland 1", "Nederland 2", "Nederland 3", "RTL 4", "RTL 5", "SBS 6", "NET 5", "RTL 7", "Talpa", "Veronica"]);
	r="";
	for i in t('tr')[1:]:
		td=i('td');
		th=i('th');
		channel=str(td[0].span.string);
		if (channel in needed):
			line="  "+channel+", "+str(td[1].div.a.string);
			if (th[1].contents[0]!=None):
				line=line+", om "+str(th[1].string)+" "+str(td[3].div.a.string);
			else:
				line=line+", en daarna niks meer";
			r=r+line+"\n";
	return r;

def trigram_grow_back(cur):
	last3wordsmatch=re.search("(([\w/\\'`]+[\s,]+){0,1}[\w/\\'`]+)$", cur);
	last3words = cur[last3wordsmatch.start():last3wordsmatch.end()];
	prefix = cur[:last3wordsmatch.start()];
	matches=(piet.db('SELECT line FROM log WHERE line like "%'+last3words+'%" LIMIT 50') or [])[1:];
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
	matches=(piet.db('SELECT line FROM log WHERE line like "%'+first3words+'%" LIMIT 50') or [])[1:];
	if (len(matches)==0): return (cur, False);
	newphrase=[re.findall("[\w/\\'`]+[\s,]+"+first3words, i[0]) for i in matches];
	newphrase=[i[0] for i in newphrase if len(i)>0];
	if (len(newphrase)==0): return (cur, False);
	line=random.choice(newphrase)+postfix;
	return (line, True);

def trigram(woord):
	if (len(woord)==0):
		rowcount=int(piet.db("SELECT count(*) from log")[1][0]);
		line=piet.db("SELECT line from log where ROWID=ABS(RANDOM()%"+str(rowcount)+")")[1][0];
		woord=random.choice(re.findall("[\w/\\'`]+", line));
	ok=True;
	while(ok):
		(woord,ok)=trigram_grow_back(woord);

	ok=True;
	while(ok):
		(woord,ok)=trigram_grow_front(woord);
	return woord;

	
def trein(regel):
	return ns(string.strip("hilversum \"diemen zuid\" "+regel));

def ns(regel):
  params=string.split(regel," ");
  i=0
  vandaag=0
  morgen=0

#parse vanstation argument
  vanStation="";
  if (len(params)==1) and (regel=="?"):
    # haal storing site op, kijk of er storing op het ns net zijn"
    inp,outp,stderr = os.popen3("lynx -source www.ns.nl/pages/index.html")
    result=outp.read()
    inp.close()
    outp.close()
    stderr.close()
    i1=string.find(result,"toringen")
    i1=string.rfind(result[:i1],"href")
    i1=string.find(result,"\"",i1)+1
    i2=string.find(result,"\"",i1)
    if (i1<0 or i2<0):
      return "Error in NS site"
    url=result[i1:i2]
    url=string.replace(url,"&amp;","&")
    inp,outp,stderr = os.popen3("lynx -dump \"http://www.ns.nl"+url+"\"")
    result=outp.read()
    inp.close()
    outp.close()
    stderr.close()
    i1=string.find(result,"Storingen")+10
    i1=string.find(result,"Storingen",i1)+10
    i2=string.find(result,"Naar boven",i1)
    i2=string.rfind(result[:i2],"[")
    lines=string.split(result[i1:i2],'\n')
    result=""
    for line in lines:
      result+=string.strip(line)
      if (len(line)>0 and (line[len(line)-1]==".")):
        result+="\n"
      else:
        result+=" "
    return string.strip(result)
  if (len(params)<1) or (len(params[0])==0):
    return "mis vertrek plaats";
  if (params[i][0]=="\""):
    while (params[i][len(params[i])-1]!="\""):
      vanStation+=params[i]+" ";
      i+=1;
      if (len(params)==i):
        return "Mis sluit \"";
    vanStation+=params[i];
    vanStation=vanStation[1:(len(vanStation)-1)];
  else:
    vanStation=params[i];
  i+=1;

#parse naarstation argument
  naarStation="";
  if (len(params)==i):
    return "mis aankomst plaats";
  if (params[i][0]=="\""):
    while (params[i][len(params[i])-1]!="\""):
      naarStation+=params[i]+" ";
      i+=1;
      if (len(params)==i):
        return "Mis sluit \"";
    naarStation+=params[i];
    naarStation=naarStation[1:(len(naarStation)-1)];
  else:
    naarStation=params[i];
  i+=1;
  if params[len(params)-1].lower()=="vandaag":
    params=params[:len(params)-1]
    vandaag=1
  if params[len(params)-1].lower()=="morgen":
    params=params[:len(params)-1]
    morgen=1
  if params[len(params)-2].lower()=="vandaag":
    params=params[:len(params)-2]+[params[len(params)]]
    vandaag=1
  if params[len(params)-2].lower()=="morgen":
    params=params[:len(params)-2]+[params[len(params)]]
    morgen=1

  if (len(params)==i):
    tijdstring="nu";
  else:
    tijdstring=params[i];
  if (tijdstring=="nu"):
    tijdstring=string.strip(time.strftime("%H:%M"));
  if (string.find(tijdstring,":")<0):
    return "Tijd "+tijdstring+" snap ik niet";
  day=string.strip(time.strftime("%d"));
  month=string.strip(time.strftime("%m"));
  year=string.strip(time.strftime("%Y"));

  tijd=string.split(tijdstring,":");
  hour=tijd[0];
  minute=tijd[1];

  timenow=str(datetime.datetime.now()).split(":")
  timenow[0]=timenow[0].split(" ")[1]

  resultstr=""
  if (vandaag!=1) and (morgen==1 or (int(timenow[0]) > int(hour) or ((int(hour)==int(timenow[0])) and (int(timenow[1]) > int(minute))))):
    # time is before now, maybe user meant this time tomorrow!
    resultstr="Tijden voor morgen:\n"
    day=string.strip((datetime.date(int(year),int(month),int(day))+datetime.timedelta(days=1)).strftime("%d"))
    month=string.strip((datetime.date(int(year),int(month),int(day))+datetime.timedelta(days=1)).strftime("%m"))
    year=string.strip((datetime.date(int(year),int(month),int(day))+datetime.timedelta(days=1)).strftime("%Y"))

#NS site is weird! First retrieve the cid
  cmd = "lynx -dump -width=200 www.ns.nl"
  inp,outp,stderr = os.popen3(cmd);
  result = outp.read();
  outp.close();
  inp.close();
  stderr.close();
  i1=string.find(result,"[1]");
  i2=string.find(result,"\n",i1);
  result=result[i1:i2];
  i1=string.find(result,"cid=")+4;
  i2=string.find(result,"&",i1);
  cid=result[i1:i2];

#Now post data
  cmd = "echo -e \"vanStation=";
  cmd += vanStation;
  cmd += "&naarStation="
  cmd += naarStation;
  cmd += "&reisdatumDag=";
  cmd += day;
  cmd += "&reisdatumMaand=";
  cmd += month;
  cmd += "&reisdatumJaar=";
  cmd += year;
  cmd += "&reisdatumUur="
  cmd += hour;
  cmd += "&reisdatumMinuut=";
  cmd += minute;
  cmd += "&reisdatumVertrekAankomst=true\" | lynx -post_data -dump \"http://www.ns.nl/servlet/Satellite?referrer=snelplanner_plus&cid=";
  cmd += cid;
  cmd += "&pagename=www.ns.nl%2FPlanner%2Fplannerplus2stap&action=js2&p=1071147988062\"";
  inp,outp,stderr = os.popen3(cmd);
  result = outp.read();
  outp.close();
  inp.close();
  stderr.close();
 
#Process output
  Warning="";
  i1=string.find(result,"Reisdetails");
  if (i1 < 0):
    errorscorrected=0;
    #Iets fout... een station niet goed ingetypt?
    i1=string.find(result," Bij `Van station'");
    if (i1 >=0 ):
      #Van station niet goed
      i1=string.find(result,"n [",i1)+3;
      i2=string.find(result,".",i1);
      errorscorrected+=1;
      Warning+=vanStation+" is veranderd in: "+result[i1:i2];
      vanStation=result[i1:i2];
    i1=string.find(result," Bij `Naar station'");
    if (i1 >=0 ):
      #Naar station niet goed
      i1=string.find(result,"Reisdoel",i1);
      i1=string.find(result,"n [",i1)+3;
      i2=string.find(result,".",i1);
      errorscorrected+=1;
      if (Warning!=""):
        Warning+=" en ";
      Warning+=naarStation+" is veranderd in: "+result[i1:i2];
      naarStation=result[i1:i2];
    if (errorscorrected==0):
      return "NS site werkt niet mee of stations bestaan niet";
    #Try again with correct data
    cmd = "echo -e \"vanStation=";
    cmd += vanStation;
    cmd += "&naarStation="
    cmd += naarStation;
    cmd += "&reisdatumDag=";
    cmd += day;
    cmd += "&reisdatumMaand=";
    cmd += month;
    cmd += "&reisdatumJaar=";
    cmd += year;
    cmd += "&reisdatumUur="
    cmd += hour;
    cmd += "&reisdatumMinuut=";
    cmd += minute;
    cmd += "&reisdatumVertrekAankomst=true\" | lynx -post_data -dump \"http://www.ns.nl/servlet/Satellite?referrer=snelplanner_plus&cid=";
    cmd += cid;
    cmd += "&pagename=www.ns.nl%2FPlanner%2Fplannerplus2stap&action=js2&p=1071147988062\"";
    inp,outp,stderr = os.popen3(cmd);
    result = outp.read();
    outp.close();
    inp.close();
    stderr.close();
    i1=string.find(result,"Reisdetails");
    if (i1<0):
      return "NS-site werkt niet mee";

  i1=string.find(result,":",i1);
  returnstring="";
  vannaar="";
  while ((i1>10) and (string.find(result[i1-2:i1+3],"tp")<0)):
#Elk station

    if (vannaar=="Vertrek: "):
      vannaar="Aankomst:";
    else:
       vannaar="Vertrek: ";

#tijd
    returnstring+=vannaar+" "+result[i1-2:i1+3];

#station en spoor
    i2=string.find(result,"]",i1);
    if (result[i2+1]=="i"):
      i2=string.find(result,"]",i2+1);
    i3=string.find(result," ",i2);
    returnstring+= " "+result[i2+1:i3];

    spoor_lus=0;
    while (spoor_lus==0):
      i2=string.find(result," ",i2+1);
      i3=string.find(result," ",i2+1);
      if (string.find(result[i2:i3],"0")>=0 or string.find(result[i2:i3],"1")>=0 or string.find(result[i2:i3],"2")>=0 or string.find(result[i2:i3],"3")>=0 or string.find(result[i2:i3],"4")>=0 or string.find(result[i2:i3],"5")>=0 or string.find(result[i2:i3],"6")>=0 or string.find(result[i2:i3],"7")>=0 or string.find(result[i2:i3],"8")>=0 or string.find(result[i2:i3],"9")>=0):
        returnstring+=" spoor:";
        spoor_lus=1;
      returnstring+= " "+string.strip(result[i2:i3]);

#volgend station
    i1=string.find(result,":",i1+1);
    returnstring+="\n";
  returnstring=resultstr+returnstring
  if (Warning!=""):
    return string.strip("Waarschuwing: "+Warning+"\n"+returnstring);
  return string.strip(returnstring);

def mytest(regel):
	piet.db("PRAGMA temp_store=2");
	return "result: "+repr(piet.db(regel))+"\n";

def tel(regel):
  naam=string.lower(regel);
  if (naam=="socrates"):
    return "socrates' telefoonnummer is 06-51825810";
  elif (naam=="weary"):
    return "weary's telefoonnummer is +31 6 5111 5487";
  elif ((naam=="semyon") or (naam=="simon")):
    return "simon's telefoonnummer is +61 2 98 03 37 59";
  else:
    params=string.split(regel," ");
    i=0;

#parse naam argument
    naam="";
    if (len(params)<1) or (len(params[0])==0):
      return "mis naam argument";
    if (params[i][0]=="\""):
      while (params[i][len(params[i])-1]!="\""):
        naam+=params[i]+" ";
        i+=1;
        if (len(params)==i):
          return "Mis sluit \"";
      naam+=params[i];
      naam=naam[1:(len(naam)-1)];
    else:
      naam=params[i];
    i+=1;

#parse plaats argument
    plaats="";
    if (len(params)==i):
      return "mis plaats argument";
    if (params[i][0]=="\""):
      while (params[i][len(params[i])-1]!="\""):
        plaats+=params[i]+" ";
        i+=1;
        if (len(params)==i):
          return "Mis sluit \"";
      plaats+=params[i];
      plaats=plaats[1:(len(plaats)-1)];
    else:
      plaats=params[i];
    cmd="wget -O - -q \"";
    cmd+="http://www.detelefoongids.nl/tginl.dll?action=white&type=search&resultsperpage=25&pagestart=1&name2=";
    cmd+=naam;
    cmd+="&name=&initials=&city=";
    cmd+=plaats;
    cmd+="&citycode=&dcity=";
    cmd+=plaats;
    cmd+="&areacode=&dname=";
    cmd+=naam;
    cmd+="&dwhere=";
    cmd+=plaats;
    cmd+="&country=&source=homepage\" | grep \"Adres=\"";
#geen idee waarom het allemaal dubbel moet, vraag dat de kpn maar
    inp,outp,stderr = os.popen3(cmd);
    result = outp.read();
    outp.close();
    inp.close();
    stderr.close();
    if (len(result)<10):
      return "Volgens de telefoongids woont er geen "+naam+" in "+plaats+", sorry";
    fresult="";
    i=0;
    while (string.find(result,"<td",i)>=0):
      if (i>0):
        fresult+="\n";
      i=string.find(result,"<td",i);
      i=string.find(result,"Naam=",i)+5;
      j=string.find(result,"Gidsnr=",i);
      fresult+=result[i:j];

    fresult=string.replace(fresult,"%20"," ");
    fresult=string.replace(fresult,"&amp;"," ");
    fresult=string.replace(fresult,"Adres=","");
    fresult=string.replace(fresult,"PC=","");
    fresult=string.replace(fresult,"Plaats=","");
    fresult=string.replace(fresult,"Telnr=","");
    return fresult;    
  return "Bla bla... functie mislukte er zal wel iets fout gegaan zijn";

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
	return "ik zal eens kijken hoe het er hier voor staat en zo nodig actie ondernemen\n";

def reloadding(params):
	params=string.split(params," ")
	if (len(params)<1) or (len(params[0])==0):
		return "reload wat?"
	else:
		if params[0]=="calc" or params[0]=="supercalc":
			import calc
			reload(calc)
			return "'t is vast gelukt";
		if params[0]=="distance" or params[0]=="Distance":
			import Distance
			reload(Distance)
			return "Distance lib ready to go";
		elif params[0]=="pistes":
			import pistes;
			reload(pistes);
			return "och, wie weet is't gelukt";
		elif params[0]=="bash":
			from bash import bash;
			reload(bash);
			return "kheb vast gereload";
		elif params[0]=="pietlib":
			import pietlib;
			reload(pietlib);
			return "tjip, een nieuwe lib!";
	return "die module ken ik niet"


def meer(params):
	a=meer_data[nick];
	if a and len(a)>0:
		return string.join(a, '\n');
	return "nah"

tweakersthreads=0;
tweakersstop=0;
def tweakers_newsthread(channel):
	global tweakersthreads, tweakersstop, tweakerslastitem;
	if (tweakersthreads>0):
		return;
	tweakersthreads+=1;

	sheettext=\
		"<xsl:stylesheet version='1.0' xmlns:xsl=\"http://www.w3.org/1999/XSL/Transform\" xsl:output=\"text\" xml:space=\"preserve\">"\
		"<xsl:template match=\"/\"><xsl:for-each select=\"/rss/channel/item/title\"><xsl:value-of select=\".\"/>\n"\
		"</xsl:for-each></xsl:template></xsl:stylesheet>";
	cmd = "wget -O - -q http://tweakers.net/feeds/mixed.xml"
	tweakerslastitem="flop";

	import libxml2
	import libxslt
	styledoc = libxml2.parseDoc(sheettext);
	style = libxslt.parseStylesheetDoc(styledoc);
	while (tweakersstop==0):
		outp = os.popen(cmd);
		x=outp.read();
		outp.close();
		doc = libxml2.parseDoc(x);
		result = style.applyStylesheet(doc, None);
		try: lines=string.split(style.saveResultToString(result), '\n')[1:5];
		except: piet.send(channel, "news failure\n"); tweakersthreads-=1; return;
		lines.append(tweakerslastitem);
		oldindex=lines.index(tweakerslastitem); lines=lines[:oldindex];
		if (len(lines)>0):
			item=lines[-1];
			tweakerslastitem=item;
			piet.send(channel, 
					random.choice(("dus, ", "let op: ", "flits: ", "maareuh, ", "gerucht: ", "ja, ", "en "))
					+item+"\n");
		doc.freeDoc();
		result.freeDoc();
		time.sleep(60*15);
	style.freeStylesheet();
	piet.send(channel, "het is weer mooi geweest met tweakers nieuws, ik stop\n");
	tweakersthreads-=1;

#thread.start_new_thread(tweakers_newsthread, ());
def tweakers(regel):
	global tweakersthreads, tweakersstop;
	if (regel=="aan"):
		tweakersstop=0;
		piet.thread("tweakers_newsthread", channel);
	elif (regel=="uit"):
		tweakersstop=1;
	else:
		return "aan of uit, hoe moeilijk kan het nou helemaal wezen?\n";
	return "uh, ok\n";

def versie(regel):
  regel=string.lower(string.strip(regel));
  if (regel=="centericq" or regel=="cicq"):
    inp,outp,stderr=os.popen3("wget -O - -q http://www.centericq.de/");
    result=outp.read()
    result=string.lower(result)
    outp.close()
    inp.close()
    stderr.close()
    version=re.search("centericq [0-9]+.[0-9]+.[0-9]+", result)
    if (version!=None):
      x=version.start()+10
      y=version.end()
      return "Laatste Centericq versie "+result[x:y]
    return "Kan het versie nummer van Centericq niet vinden"
  if (regel[:5]=="linux"):
    inp,outp,stderr=os.popen3("wget -O - -q http://kernel.org/kdist/rss.xml")
    result=outp.read()
    result=string.lower(result)
    outp.close()
    inp.close()
    stderr.close()
    version=re.search("[0-9]+.[0-9]+.[0-9]+(.[0-9]+)?: stable", result)
    if (version!=None):
      version=result[version.start():version.end()]
      x=string.find(version,":")
      return "Laatste linux kernel versie "+version[:x]
    return "Kan het laatste versie nummer van de linux kernel niet vinden"
  if len(regel)==0:
    return "ik ben nu versie "+str(random.randint(0,9))+"."+str(random.randint(0,9))+", maar dat kan straks wel anders wezen";
  return regel+" ken ik niet"


d={ "anagram":           (100, anagram, "bedenk een anagram, gebruik anagram <woorden> of anagram en <woorden> om engels te forceren."),
    "verklaar":          (100, verklaar, "Zoekt op het internet wat <regel> is"),
    "dw":                (100, discw, "dw <speler>, bekijkt de inlog status van <speler> op discworld"),
    "dwho":              (100, discwho, "dwho, kijk wie van Taido, Irk, Weary of Szwarts op discworld zijn"),
    "galgje":            (150, galgje, "spel een spelletje galgje, begin met galgje start en daarna galgje raad <letter>"),
    "vandale":           (100, vandale, "vandale <woord>, zoek woord op in woordenboek"),
    "urban":             (100, urban, "urban <woord>, zoek woord op in urbandictionary (warning: explicit content)"),
    "rijm":              (100, rijm, "rijm <woord>, zoek rijmwoorden op"),
    "vertaal":           (100, vertaal, "vertaal <brontaal> <doeltaal> <regel>, vertaalt <regel> van de taal <brontaal> naar de taal <doeltaal>"),
    "weer":              (100, weer, "weer, zoek het weer op"),
    "zeg":               (0, zeg, "zeg <text> [tegen <naam>|op <channel>], ga napraten"),
		"rot":             (0, rot_nr, "rot<nr> <text>, versleutel <text> met het rot<nr> algorithme"),
    "ping":              (100, ping, "ping, zeg pong"),
    "remind":            (300, remind, "remind <time> <message>, wacht <time> seconden en zeg dan <message>"),
    "sin?":              (500, sin, "sin, lookup sin's ip-address"),
    "nmblookup":         (500, nmblookup, "nmblookup <host>, zoek op campusnet naar een ip"),
    "PING":              (100, ping, ""),
    "hallo?":            (100, ping, ""),
    "afk":               (100, afk, "afk <afk>, zoek een afkorting op"),
    "spel":              (0, spell_nl, "spel <woord/zin>, spellcheck een woord/zin in het nederlands"),
    "spell":             (0, spell_en, "spell <woord/zin>, spellcheck een woord/zin in het engels"),
    "zauber":            (0, spell_de, "zauber <woord/zin>, spellcheck een woord/zin in het duits"),
    "buchstabieren":     (0, spell_de, ""),
    "schreiben":         (0, spell_de, ""),
    "schreib":           (0, spell_de, ""),
    "changelog":         (1000, changelog, "changelog, show the recent changes to piet"),
    "help":              (0, help, ""),
    "calc":              (0, supercalc, ""),
    "reken":             (0, supercalc, "reken uit <expressie> rekent iets uit via de internal piet-processer\nvoor help doe reken help"),
    "alias":             (1000, alias, ""),
    "stop":              (1000, leeg, "stop [<reden>], ga van irc"),
    "ga weg":            (1000, leeg, "ga weg [van <kanaal>], /leave <kanaal>"),
    "kom bij":           (1000, leeg, "kom bij <kanaal>, /join <kanaal>"),
    "doe":               (1200, leeg, "doe <commando>, voer een shell-commando uit"),
    "nieuws":            (100, news, "nieuws, laat de recente nieuwsheaders zien"),
    "temp":              (0,temp, "temp, de temperatuur van sommige plaatsen in de wereld"), 
    "watis":             (1000, watis, "watis <iets>, geeft veel bla over <iets>"),
    "dict":             (1000, watis, ""),
    "kop dicht":         (1000, leeg, "kop dicht, hou op met spammen"),
		"auth iedereen":     (1200, auth_iedereen, "auth iedereen, geef iedereen authorisatie 1000 (inclusief jezelf)"),
    "auth":              (-6, change_auth, "auth [<niveau> <nick> [<paswoord>]], geef een authenticatieniveau"),
    "spreuk":            (0, spreuk, "spreuk, geef een leuke(?) spreuk"),
    "oneliner":          (0, spreuk, ""),
    "ping":              (100, ping, "ping <host>, ping een computer"),
    "dvorak2qwerty":     (0, dvorak2qwerty, "dvorak2qwerty <text>, maak iets dat op een qwerty-tb in dvorak is getikt leesbaar"),
    "d2q":               (0, dvorak2qwerty, ""),
		"datum":             (100, datum, "geef de datum van vandaag"),
    "dat":               (100, last, "dat [x], herhaal wat er x regels terug gezegd werd"),
    "leet":              (0, leet, "leet <text>, convert to 1337"),
    "unleet":            (0, unleet, "unleet <text>, unconvert to 1337"),
    "todo":		 (1, todo, "todo <text>, voeg wat toe aan de todo list"),
    "bugrep":		 (1, todo, ""),
    "geordi":		 (0, geordi, ""),
    "geoip":             (100, geoip, "geoip <ip>, zoekt positie op aarde van ip"),
    "je heet nu":        (500, jeheetnu, "je heet nu <nick>, geef nieuwe nick"),
    "renick":            (200, randomnaam, "renick, verzint een willekeurige nick"),
    "opme":              (500, opme, "opme, geef @"),
    "koffie?":           (121, leeg, "koffie?, vraag of ie koffie wil"),
    "simon?":            (100, simon, "simon?, kijkt of simon op sorcsoft ingelogd is"),
    "citaat":            (100, citaat, "citaat, geeft een random regel text die ooit gezegd is"),
    "context":            (100, context, "context <text>, geeft de context waarin iets gezegd is"),
    "wees stil":         (1000, leeg, "wees stil, laat piet z'n kop houden met loze dingen"),
    "stil?":             (1000, leeg, "stil?, probeert piet zich stil te houden?"),
    "praat maar":        (1000, leeg, "praat maar, tegenovergestelde van \"wees stil\""),
    #"lees lua":          (1000, leeg, "lees lua, herlees het lua script"),
    "kies":              (100, kies, "kies een willekeurig woord uit de opgegeven lijst"),
    "tv":                (100, tv_nuenstraks, "geef overzicht van wat er op tv is"),
		"trigram":					 (1000, trigram, "praat nonsens"),
    "url":               (100, url, "geef willekeurige oude url"),
    "versie":            (100, versie, "versie <x> zoekt laatste versie op van software dinges"),
    "version":           (100, versie, ""),
    "mep":               (100, mep, ""),
    "geef":              (100, geef, ""),
		"pistes":            (100, cmd_pistes, "pistes, doet iets met skipistes"),
		"bash":								(100, bash, "Geef bash quote <nummer> terug of een random bashquote bij gebrek aan nummer"),
		"sentence":          (100, random_sentence, "sentence, geef een willekeurige engelse zin"),
    "dum":               (0, dum, ""),
    "wiki":		 (500, wiki, "wiki <woord> Freeware encyclopedie"),
    "tel":               (1000, tel, "geef weary's mobielnr"),
    "tweakers":               (1000, tweakers, "zet nieuws vanaf tweakers.net aan/uit"),
    "tijd":		 (0, tijd, "tijd, geeft aan hoe laat het is in Sydney en Amsterdam"),
    "tijdzone":		 (1000, tijdzone, "tijdzone [naam [tijdzone]], verander tijdzones van mensen. zie /usr/share/zoneinfo."),
    "ns":                (100, ns, "ns <vertrekplaats> <aankomstplaats> <tijd>"),
    "hoever":            (100, Distance.Distance, "hoever <van> <naar>"),
    "afstand":            (100, Distance.Distance, ""),
    "distance":            (100, Distance.Distance, ""),
    "trein":                (1200, trein, ""),
    "quote":             (1000, quote, "quote <add> <regel> om iets toe te voegen of quote om iets op te vragen"),
    "reload":            (1000, reloadding, "reload <module> reload iets voor piet"),
		"uptime":            (200, uptime, "uptime, verteld tijd sinds eerste python command"),
		"zoek":              (1000, zoek, "zoek vrouw, zoekt willekeurige vrouw in overijsel"),
		"hex":               (101, hex2dec, "hex <nummer>, reken van/naar hex"),
		"meer":              (200, meer, "meer, geef nog's wat meer output van vorig commando"),
    "test": (100, mytest, "ding"),
    "onbekend_commando": (0, onbekend_commando, "")};

#param_org: string containing command+parameters
#first: True for outer call, False for recursions
#magzeg: allways True
def parse(param_org, first, magzeg):
	global auth,nick;

	# check of het een calc commando is en voeg dan calc toe voor  het commando
	param_org=addcalc(param_org)

	command="";
	params=param_org;
	for x in d:
		if param_org.startswith(x) and len(x)>len(command):
			command=x;
			params=string.strip(param_org[len(command):]);

	if (command==""):
		if (first):
			command="onbekend_commando";
		else:
			command="zeg";
	
	print (command, params, int(auth));
	
	functie=d[command];
	if (int(auth)<functie[0]):
		if (first):
			functie=d["onbekend_commando"];
		else:
			functie=d["zeg"];
			params=param_org;
  
	r="";
	if (int(auth)>=functie[0]):
		if (functie==d["zeg"]) and (magzeg==False):
			r=params;
		else:
			r=functie[1](params);

	meer_data[nick]=[]
	maxlines=10;
	r2=[i for i in string.split(r, '\n') if len(string.strip(i))>0];
	if (len(r2)>maxlines):
		l=str(len(r2));
		meer_data[nick]=r2[maxlines:];
		r=string.join(r2[:maxlines], '\n')+"\n"+nick+": de rest verzin je zelf maar, "+str(maxlines)+" van de "+l+" regels vind ik zat\n";
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
	print "channel is now ", channel;
	print "executing", nick, auth, channel, msg_;
	result=parse(msg_, True, True);
	piet.send(channel_, result);

