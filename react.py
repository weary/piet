#!/usr/bin/python

import sys, random, re, time, BeautifulSoup, traceback, urllib;
sys.path.append(".");
import piet;
import pietlib;

#execfile("random_line.py");

def get_url_title(channel, url):
	if url[0:4].lower()!="http": url="http://"+url;
	if len(url)>0 and url[-1]=='?': url=url[0:-1];
	try:
		url_input=pietlib.get_url(url);
	except:
		piet.send(channel, "nou, dat lijkt misschien wel wat op een url, maar 't bestaat niet hoor\n");
		traceback.print_exc();
		return;
	
	tinyurl="dat ding";
	if len(url)>60:
		apiurl = "http://tinyurl.com/api-create.php?url=";
		tinyurl = urllib.urlopen(apiurl + url).read();

	try:
		soup = BeautifulSoup.BeautifulSoup(url_input)
		piet.send(channel, "de titel van "+tinyurl+" is: "+soup.html.title.string+"\n")
		if url.find('divx.com'):
			value = dict(soup.input.attrs)['value']
			value = urllib.unquote(value)
			value = value.replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"')
			print repr(value)
			soup2 = BeautifulSoup.BeautifulSoup(value)
			movieurl = dict(soup2.embed.attrs)['src']
			piet.send(channel, "maar eigenlijk is dit het filmpje: " + movieurl + "\n")
	except:
		traceback.print_exc()

def do_search_replace(channel, nick, regmatchobj, lastchat):
	try:
		matchstring = regmatchobj.group();
		matchresult = matchstring.split('/');

		fromstring = matchresult[1];
		tostring = matchresult[2];

		if(lastchat[0:7] == "\001ACTION"):
			lastchat = "* " + nick + lastchat[7:len(lastchat)-1];

		replaceresult = lastchat.replace(fromstring, tostring);
		if(replaceresult != lastchat):
			piet.send(channel, "Volgens mij bedoelde " + nick + " dit: " + replaceresult);
			return replaceresult;
		else:
			return False;
	except:
		traceback.print_exc();
		return False;


#create table paginas(tijd integer, nick text, paginas integer)
def check_pagina(channel, nick, paginas):
  try:
    paginas=int(paginas);
    nu=int(time.time());
    piet.db("INSERT INTO paginas VALUES("+str(nu)+", \""+nick+"\", "+str(paginas)+");");
    first=piet.db("SELECT tijd,paginas FROM paginas WHERE nick=\""+nick+"\" ORDER BY tijd LIMIT 1")[1];
    first=[int(a) for a in first]
    prev=int(piet.db("SELECT paginas FROM paginas WHERE nick=\""+nick+"\" ORDER BY tijd DESC LIMIT 2")[2][0]);

    # sinds vorige keer
    mutatie=paginas-prev;
    r="";
    if mutatie>1:
        r="dat zijn er weer "+str(mutatie);
    elif mutatie>0:
        r="weer eentje dus";
    elif mutatie<-1:
        r="hee, dat zijn er "+str(-mutatie)+" minder"
    elif mutatie<0:
        r="pagina'tje minder, altijd goed"
    else:
        r="echt opschieten doet't niet"
    
    # sinds begin
    dpag=paginas-int(first[1]);
    dtijd=nu-int(first[0]);
    d=float(dpag)/dtijd;
    d=d*60; eenheid="minuut";
    if abs(d)<0.5:
        d=d*(24*60);
        eenheid="dag";
    if abs(d)<0.5:
        d=d*7;
        eenheid="week";
    if abs(d)<0.5:
        d=d*52;
        eenheid="jaar";
    d=round(d,2);
    
    r=r+" (ongeveer "+str(d)+" per "+eenheid+")";
    piet.send(channel, r)
  except:
    traceback.print_exc();

if not(vars().has_key("lastnicklog")):
	lastnicklog = {};

def do_react(channel, nick, pietnick, auth_, line):
	reactfile = "react.txt"
	loosfile = "loos.txt"
	logfile = "log.txt"

	line = line.replace(pietnick, "piet");

	# ok, alles in een file
	inf = open(reactfile)
	lines = inf.read().split('\n')
	inf.close()

	# laatste regel even in een logfile
	inf = open(logfile, "a+");
	inf.write(line+"\n");
	inf.close();

	ready=False;

	if lastnicklog.has_key(nick) and lastnicklog[nick]==line:
		r=random.choice([
				"ja, zeg het vooral nog's",
				"spannend hoor, zo'n herhaling",
				"gave opmerking, zeg",
				"blij dat je dat nog's zegt",
				line,
				"ah, ja, dat. verstond je niet de 1e keer",
				"s/"+line+"//"]);
		piet.send(channel, r+"\n");
		ready=True;

	# check for url's in the input
	urlmatch=re.search("((https?://|www\.)[^ \t,]*)", line);
	if (urlmatch):
		get_url_title(channel, urlmatch.group(0));
		ready=True;

	paginamatch=re.search("([0-9]{2,3})[ ]*pagina", line);
	if (paginamatch):
		check_pagina(channel, nick, paginamatch.group(1));
		ready=True;

	nicklogset = False;
	if not(ready):
		try:
			srmatch = re.match("^(s[/][A-Za-z0-9 ]+[/][A-Za-z0-9 ]*[/]?)$", line);
			if srmatch:
				sr_result = do_search_replace(channel, nick, srmatch, lastnicklog[nick]);
				if sr_result:
					lastnicklog[nick] = sr_result;
					nicklogset = True;
					ready=True;
		except:
			# Not gonna happen
			traceback.print_exc();

	if not(nicklogset):
		lastnicklog[nick] = line;

	random.seed();
	i=0;
	result="";
	while (i<len(lines)) and not(ready):
		try:
			excludethis=False;
			if (lines[i].count('#')==2):
				(keyw, chance, reactline) = lines[i].split('#');
				exclude="";
			else:
				(keyw, chance, reactline,exclude) = lines[i].split('#',3);
				if (exclude.count('#')==0):
					excludethis=(line.find(exclude)!=-1);
				else:
					for excludeword in exclude.split('#'):
						if (line.find(excludeword)!=-1):
							excludethis=True;
			r=random.random();
			
			if not(excludethis):
				if (line.find(keyw)!=-1) and (random.random()<=float(chance)):
					ready=True;
					result=reactline;
		except:
			result="";
		i=i+1;

	if not(ready):
		r=random.random();
		if (r<=0.06):
			if globals().has_key("geordi") and (random.random()<0.08):
				n=random.randint(1,4000);
				time.sleep(n);
				result=geordi("bla");
			else:
				inf = open(loosfile);
				lines = inf.read().split('\n');
				inf.close();
				result=random.choice(lines);

	if result[:6]=="ACTION":
		result = "\001"+result+"\001";
	if (len(result)>0):
		result=result.replace("NICK", nick);
		result=result.replace("piet", pietnick);
		piet.send(channel, result+"\n");
	
