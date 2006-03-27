#!/usr/bin/python

import sys,string,random,re,time,BeautifulSoup,traceback;
import piet;
import pietlib;

#execfile("random_line.py");

def get_url_title(channel, url):
	if url[0:4].lower()!="http": url="http://"+url;
	try:
		input=pietlib.get_url(url);
	except:
		piet.send(channel, "nou, dat lijkt misschien wel wat op een url, maar 't bestaat niet hoor\n");
	try:
		soup=BeautifulSoup.BeautifulSoup(input);
		piet.send(channel, "de titel van dat ding is: "+soup.html.title.string+"\n");
	except:
		traceback.print_exc();

def do_search_replace(channel, nick, regmatchobj, lastchat):
	try:
		matchstring = regmatchobj.group();
		matchresult = string.split(matchstring, '/');

		fromstring = matchresult[1];
		tostring = matchresult[2];

		if(lastchat[0:7] == "\001ACTION"):
			lastchat = "* " + nick + lastchat[7:len(lastchat)-1];

		replaceresult = string.replace(lastchat, fromstring, tostring);
		if(replaceresult != lastchat):
			piet.send(channel, "Volgens mij bedoelde " + nick + " dit: " + replaceresult);
			return replaceresult;
		else:
			return False;
	except:
		return False;
		
try:
	lastnicklog;
except:
	lastnicklog = {};
	
def do_react(channel, nick, pietnick, line):
	reactfile = "react.txt"
	loosfile = "loos.txt"
	logfile = "log.txt"

	#fname = string.strip(sys.stdin.readline());
	line = string.replace(line, pietnick, "piet");

	# ok, alles in een file
	inf = open(reactfile);
	lines = string.split(inf.read(), '\n');
	inf.close();

	# laatste regel even in een logfile
	inf = open(logfile, "a+");
	inf.write(line+"\n");
	inf.close();

	ready=False;

	# check for url's in the input
	urlmatch=re.search("((https?://|www\.)[^ \t]*)", line);
	if (urlmatch):
		get_url_title(channel, urlmatch.group(0));
		ready=True;

	nicklogset = False;
	if(not(ready)):
		try:
			lastchat = lastnicklog[nick];
			srmatch = re.match("^(s[/][A-Za-z0-9 ]+[/][A-Za-z0-9 ]*[/]?)$", line);
			if(srmatch):
				sr_result = do_search_replace(channel, nick, srmatch, lastnicklog[nick]);
				if(sr_result):
					lastnicklog[nick] = sr_result;
					nicklogset = True;
					ready=True;
		except:
			# Not gonna happen
			3;

	if(not(nicklogset)):
		lastnicklog[nick] = line;

	random.seed();
	i=0;
	result="";
	while (i<len(lines)) and (not(ready)):
		try:
			excludethis=False;
			if (string.count(lines[i],'#')==2):
				(keyw, chance, reactline) = string.split(lines[i],'#');
				exclude="";
			else:
				(keyw, chance, reactline,exclude) = string.split(lines[i],'#',3);
				if (string.count(exclude,'#')==0):
					excludethis=(string.find(line,exclude)<>-1);
				else:
					for excludeword in string.split(exclude,'#'):
						if (string.find(line,excludeword)<>-1):
							excludethis=True;
			r=random.random();
			
			if (excludethis==False):
				if (string.find(line, keyw)<>-1) and (random.random()<=float(chance)):
					ready=True;
					result=reactline;
		except:
			result="";
		i=i+1;

	if (not(ready)):
		r=random.random();
		if (r<=0.06):
			if (random.random()<0.08):
				n=random.randint(1,4000);
				time.sleep(n);
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
					result="Captain, "+A;
			else:
				inf = open(loosfile);
				lines = string.split(inf.read(), '\n');
				inf.close();
				result=random.choice(lines);

	if result[:6]=="ACTION":
		result = "\001"+result+"\001";
	if (len(result)>0):
		result=string.replace(result, "NICK", nick);
		result=string.replace(result, "piet", pietnick);
		piet.send(channel, result+"\n");
	
