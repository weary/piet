#!/usr/bin/python
# -*- coding: iso-8859-1 -*-

import sys,string,random,re,os,time;
from telnetlib import Telnet;

todofile = "todo.txt";
logfile = "log.txt";

nick = string.strip(sys.stdin.readline());
auth = int(string.strip(sys.stdin.readline()));
channel = string.strip(sys.stdin.readline());
msg = string.strip(sys.stdin.readline());
d={};
#print ("1", nick, auth, channel, msg);

def parse(param, first, magzeg):
  print "HELP! PIET STUK\n";
  return "";


def leeg(param):
  return "";

def onbekend_commando(param):
  if (len(param)==0):
    return "ok\n";
  elif (random.random()>=0.475):
    return "ja\n";
  elif (random.random()>=0.95):
    return "nee\n";
  return "euh...\n";

def convert(char):
  if (char=="\xb4"):
    return "";
  elif (char=="\xb7"):
    return ".";
  else:
    return char;

def kies(params):
  params = string.strip(parse(params, False, True));
  list=string.split(params," ");
  if (len(list)==0):
    return "Ik kies een appel";
  return random.choice(list);


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
  comm="lynx --dump \"http://www.rijmwoorden.nl/rijm.pl?woord="+string.strip(woord)+"&stap=2\" | head -10 | tail -n 4";
  inp = os.popen(comm);
  result=inp.read();
  if (re.search("Unable to connect", result)!=None):
    return "rijmwoorden stuk, echt\n";
  else:
    if (re.search("Helaas, geen woorden gevonden", result)!=None):
      return "geen rijmwoorden gevonden\n";
    else:
      result=string.split(result, '\n');
      result=[re.sub("\s+", ", ", string.strip(i)) for i in result];
      result=string.join(result, "\n");
      return result+"\n";

def makeenterfromnull(inp):
  if inp=="":
    return "\n";
  else:
    return inp;
  
def weer(woord):
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

def zeg(params):
  params = string.strip(parse(params, False, False));
  a=string.split(params, ' ');
  try:
    b=a.index("tegen");
    name=a[b+1];
    del a[b:b+2];
    a=[name+",", "ehm,"]+a;
  except:
    a=a;
  return string.join(a, ' ')+"\n";

def rot13(params):
  params = string.strip(parse(params, False, True));
  inp, outp = os.popen2("tr A-Za-z N-ZA-Mn-za-m");
  inp.write(params);
  inp.close();
  return outp.read()+"\n";

def afk(woord):
	result1=afk_hylke(woord);
	result2=afk_eelco(woord);	
	result=result1 + result2;
	if (len(result)==0):
		r="Geen afkortingen gevonden voor "+woord+"\n";
	elif (len(result)==1):
		try:
			r=result[0][0]+" staat voor \""+result[0][1]+"\", "+result[0][2]+"\n";
		except:
			r="";
			print "piet failure: ",result;
	else:
		r="ik ken "+str(len(result))+" verklaringen voor "+woord+", namelijk:\n";
		for i in result:
			try:
				r+="  "+i[0]+": \""+i[1]+"\", "+i[2]+"\n";
			except:
				r="";
				print "piet failure: ",result;
	return r;
	
def afk_hylke(woord):
  woord=string.strip(woord);
  comm="lynx -source http://www.afkorting.nl/cgi-local/s.pl?pg=a\&s="+woord;
  outp, inp = os.popen2(comm);
  outp.close();
  result=inp.read();
  result=re.findall("<TR>.*</TR>", result);
  result=[re.findall("<T[DH]>[^<]*</T[DH]>", i) for i in result];
  result=[[i[4:-5] for i in result_inner] for result_inner in result];
  return result;

def changelog(dinges):
  command="darcs cha --last=5 | sed -e '/^$/d;N;s/\\n//g;s/<[a-zA-Z]\\+@[a-zA-Z\\.]\\+>//;s/[\\t\\ ]\\+/ /g'";
  inp = os.popen(command);
  result=inp.read();
  inp.close();
  return "echt veel is er niet veranderd...\n"+result;


def afk_eelco(woord):
  inf = open("afk.txt");
  lines = string.split(inf.read(), '\n');
  i=0;
  result=[];
  while (i<len(lines)):
    try:
      (keyw, reactline) = string.split(lines[i], '#');
      search0=keyw
      search1=string.upper(keyw);
      search2=string.lower(keyw);
      search3=keyw+".";
      search4="";
      for j in keyw:
        search4+=j+'.';
      found=[];
      if (woord == search0):
        if (reactline not in found):
          result+=[[keyw,reactline,'-']];
          found+=[reactline];
      if (woord == search1):
        if (reactline not in found):
          result+=[[keyw,reactline,'-']];
          found+=[reactline];
      if (woord == search2):
        if (reactline not in found):
          result+=[[keyw,reactline,'-']];
          found+=[reactline];
      if (woord == search3):
        if (reactline not in found):
          result+=[[keyw,reactline,'-']];
          found+=[reactline];
      if (woord == search4):
        if (reactline not in found):
          result+=[[keyw,reactline,'-']];
          found+=[reactline];
    except:
      result+="";
    i=i+1;
  return result;
	
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
    result="ik ben opeens vergeten hoe je dit naar het "+doel+" vertaalt.";
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

def tv(params):
  return("er is niks op tv");

def news(params):
  cmd="lynx -dump -width=500 http://www.trouw.nl/ANP/LAATSTE_NIEUWS/";
  cmd=cmd+"| sed -ne \"/blokje.gif/{s/\\[[a-z0-9\\.]*\\]//g;s/\\ \\ //g;/^.*bal:/b;/^Tennis:/b;/^Schaatsen:/b;p}\"";
  inp = os.popen(cmd);
  result=inp.read();
  return(result);

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
    result="niemand!";
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

def to_int(in_str):
  out_num = 0;
  result =0;
  for x in range(0,len(in_str)):
    if (in_str[x]=='d'):
      result += 86400*out_num;
      out_num=0;
    elif (in_str[x]=='h'):
      result +=3600*out_num;
      out_num=0;
    elif (in_str[x]=='m'):
      result += 60*out_num;
      out_num=0;
    elif (in_str[x]=='s'):
      result += out_num;
      out_num=0;
    else:
      if ((ord(in_str[x]) < ord('0')) or (ord(in_str[x]) > ord('9'))):
        return -1;
      out_num = out_num * 10 + ord(in_str[x]) - ord('0')
  result += out_num;
  return result;

def remind(regel):
  params=string.split(regel, ' ');
  if (len(params) < 2):
    return "heb tijd en bericht nodig voor remind";
  tijd = to_int(string.strip(params[0]));
  if (tijd < 0):
    return "tijdsaanduiding klopt niet";
  time.sleep(tijd);
  result = string.join(params[1:]);
  return string.strip(parse(result, False, True));

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
    return "\001ACTION mept er lustig op los \001";
  r=random.random();
  if (r<=0.1):
    return "ik zou niet weten waarom";
  if (r<=0.2):
    return "\001ACTION mept "+nick+" zelf";
  if (r<=0.5):
    return "\001ACTION deelt een corrigerende mep uit aan "+params[0];
  return "\001ACTION mept "+params[0];

def geef(regel):
  params=string.split(regel,' ');
  if (len(params)<1) or (len(params[0])==0):
    return "\001ACTION geeft "+nick+" een blik van verstandhouding";
  i=0;
  before="";
  line="";
  for a in params:
    before+=a+" ";
    if a=="aan":
      line=before;
  if (line!=""):
    return "\001ACTION geeft "+before+"\001";
  return "\001ACTION deelt "+params[0]+" "+string.join(params[1:],' ')+" uit";

def calc(regel):
  params=string.split(regel,' ');
  if (len(params)<1) or (len(params[0])==0):
    return "Internal piet processor halted, nothing to calculate bailing out";
  regel = string.strip(parse(regel, False, True));
  cmd="echo \""+regel+"\" | bc";
  inp,outp,stderr=os.popen3(cmd);
  result=outp.read();
  outp.close();
  inp.close();
  stderr.close();
  return result;

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

def temp(regel):
  params=string.split(regel, ' ');
  if (len(params)<1) or (len(params[0])==0):
    params=string.split("Enschede Sydney",' ');

  result="";
  for City in params:
    if (string.lower(City)=="e'de" or City=="enschede" or string.lower(City)=="twente" or string.lower(City)=="twenthe"):
      City="Enschede";
    if (string.lower(City)=="r'dam" or City=="rotterdam" or string.lower(City)=="rdam"):
      City="Rotterdam";
    if (string.lower(City)=="nsw" or City=="sydney"):
      City="Sydney";
    if (string.lower(City)=="h'sum" or City=="hilversum" or string.lower(City)=="hsum"):
      City="Hilversum";
    url="";
    if (City=="Enschede"):
      url="http://www.wunderground.com/global/stations/06290.html";
# First Entry from table for Ensched
      t=1;
    if (City=="Sydney"):
      url="http://www.wunderground.com/global/stations/94767.html";
# Second Entry from table for Sydney
      t=2;
    if (City=="Rotterdam"):
      url="http://www.wunderground.com/global/stations/06344.html";
      t=1;
    if (City=="Hilversum"):
      url="http://www.wunderground.com/cgi-bin/findweather/getForecast?query=hilversum";
      t=2;
    if (url==""):
      return "ken geen "+City;
    cmd="wget -O - -q "+url;
    i1=1;
    data="";
    tries=5;
    while (i1<10 and tries>0):
      inp,outp,stderr = os.popen3(cmd);
      data = outp.read();
      outp.close();
      inp.close();
      stderr.close();
      i1=string.find(data,"<b>Updated:");
      tries-=1;
    if (tries<=0):
      return "Site werkt niet mee... Geen info";
#Add City name to string
    result += City+", ";
#Add local time to string
    i1=1;
    while (t>0):
      i1 = string.find(data,"<b>Updated:",i1)+12;
      t-=1;
    i2 = string.find(data,"</b>",i1);
    result += data[i1:i2]+": ";
#Add temp info
    i2 = string.find(data,"&#176;C",i2);
    i2 = string.rfind(data[:i2],"</b>");
    i1 = string.rfind(data[:i2],"<b>")+3;
    result += data[i1:i2]+"°C, luchtvochtigheid = ";
#Add humidity info
    i2 = string.find(data,"%</",i2);
    i1 = string.rfind(data[:i2],"<b>")+3;
    result += data[i1:i2]+"%, wind = ";
#Add Wind info
    i1 = string.find(data,"<td",i2);
    if (string.find(string.lower(data[i1:i1+150]),"calm")>1):
      result+="Calm";
    else:
      i2 = string.find(data,"km/h",i2);
      i1 = string.rfind(data[:i2],"/")+1;
      if (string.find(data[i1:i2],"nbsp;")>0):
        i1 = string.rfind(data[:i2],"<b>")+3;
        i2 = string.find(data,"</b",i1);
      result+=data[i1:i2]+"km/h";
    result+='\n';
  result=string.strip(result);
  return result;

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
  tijdstruct=time.gmtime();
  localstruct=time.localtime();
  result= "NL: "+str(localstruct[3])+":";
  if (localstruct[4] < 10):
    result += "0";
  result+=str(tijdstruct[4])+"  NSW: ";
  diff=(localstruct[3]-tijdstruct[3]);
  while (diff < 0):
    diff+=24;
  if (diff==2):
    if (localstruct[3]>15):
      result += str(localstruct[3]-16);
    else:
      result += str(localstruct[3]+8);
  else:
    if (localstruct[3]>13):
      result += str(localstruct[3]-14);
    else:
      result += str(localstruct[3]+10);
  result +=":";
  if (localstruct[4] < 10):
    result += "0";
  result += str(localstruct[4]);
  return result;

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

def trein(regel):
	return ns("hilversum \"diemen zuid\" "+regel);

def ns(regel):
  params=string.split(regel," ");
  i=0;

#parse vanstation argument
  vanStation="";
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
  if (Warning!=""):
    return string.strip("Waarschuwing: "+Warning+"\n"+returnstring);
  return string.strip(returnstring);
  

def tel(regel):
  naam=string.lower(regel);
  if (naam=="socrates"):
    return "socrates' telefoonnummer is 06-51825810";
  elif (naam=="weary"):
    return "weary's telefoonnummer is +31 6 5111 5487";
  elif ((naam=="semyon") or (naam=="Semyon") or (naam=="simon")):
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

d={ "anagram":           (100, anagram, "bedenk een anagram, gebruik anagram <woorden> of anagram en <woorden> om engels te forceren."),
    "verklaar":          (100, verklaar, "Zoekt op het internet wat <regel> is"),
    "dw":                (100, discw, "dw <speler>, bekijkt de inlog status van <speler> op discworld"),
    "dwho":              (100, discwho, "dwho, kijk wie van Taido, Irk, Weary of Szwarts op discworld zijn"),
    "galgje":            (150, galgje, "spel een spelletje galgje, begin met galgje start en daarna galgje raad <letter>"),
    "vandale":           (100, vandale, "vandale <woord>, zoek woord op in woordenboek"),
    "rijm":              (100, rijm, "rijm <woord>, zoek rijmwoorden op"),
    "vertaal":           (100, vertaal, "vertaal <brontaal> <doeltaal> <regel>, vertaalt <regel> van de taal <brontaal> naar de taal <doeltaal>"),
    "weer":              (100, weer, "weer, zoek het weer op"),
    "zeg":               (0, zeg, "zeg <text> [tegen <naam>], ga napraten"),
    "ping":              (100, ping, "ping, zeg pong"),
    "remind":            (1000, remind, "remind <time> <message>, wacht <time> seconden en zeg dan <message>"),
    "sin?":              (500, sin, "sin, lookup sin's ip-address"),
    "nmblookup":         (500, nmblookup, "nmblookup <host>, zoek op campusnet naar een ip"),
    "PING":              (100, ping, ""),
    "hallo?":            (100, ping, ""),
    "rot13":             (0, rot13, "rot13 <text>, doe een rot13 op text"),
    "afk":               (100, afk, "afk <afk>, zoek een afkorting op"),
    "spel":              (0, spell_nl, "spel <woord/zin>, spellcheck een woord/zin in het nederlands"),
    "spell":             (0, spell_en, "spell <woord/zin>, spellcheck een woord/zin in het engels"),
    "zauber":            (0, spell_de, "zauber <woord/zin>, spellcheck een woord/zin in het duits"),
    "buchstabieren":     (0, spell_de, ""),
    "schreiben":         (0, spell_de, ""),
    "schreib":           (0, spell_de, ""),
    "changelog":         (1000, changelog, "changelog, show the recent changes to piet"),
    "help":              (0, help, ""),
    "calc":              (0, calc, "calc <expressie> rekent iets uit via de internal piet-processer"),
    "alias":             (1000, alias, ""),
    "stop":              (1000, leeg, "stop [<reden>], ga van irc"),
    "ga weg":            (1000, leeg, "ga weg [van <kanaal>], /leave <kanaal>"),
    "kom bij":           (1000, leeg, "kom bij <kanaal>, /join <kanaal>"),
    "doe":               (1200, leeg, "doe <commando>, voer een shell-commando uit"),
    "nieuws":            (100, news, "nieuws, laat de recente nieuwsheaders zien"),
    "temp":              (0,temp, "temp, de temperatuur in Twente en in NSW"), 
    "watis":             (1001, watis, "watis <iets>, geeft veel bla over <iets>"),
    "kop dicht":         (1000, leeg, "kop dicht, hou op met spammen"),
    "auth":              (0, leeg, "auth <niveau> <nick> [<paswoord>], geef een authenticatieniveau"),
    "spreuk":            (0, spreuk, "spreuk, geef een leuke(?) spreuk"),
    "oneliner":          (0, spreuk, ""),
    "ping":              (100, ping, "ping <host>, ping een computer"),
    "dvorak2qwerty":     (0, dvorak2qwerty, "dvorak2qwerty <text>, maak iets dat op een qwerty-tb in dvorak is getikt leesbaar"),
    "d2q":               (0, dvorak2qwerty, ""),
    "dat":               (100, last, "dat [x], herhaal wat er x regels terug gezegd werd"),
    "leet":              (0, leet, "leet <text>, convert to 1337"),
    "unleet":            (0, unleet, "unleet <text>, unconvert to 1337"),
    "todo":		 (1, todo, "todo <text>, voeg wat toe aan de todo list"),
    "bugrep":		 (1, todo, ""),
    "tv":                (0, tv, ""),
    "geordi":		 (0, geordi, ""),
    "je heet nu":        (500, leeg, "je heet nu <nick>, geef nieuwe nick"),
    "renick":            (200, randomnaam, "renick, verzint een willekeurige nick"),
    "opme":              (150, leeg, "opme, geef @"),
    "koffie?":           (121, leeg, "koffie?, vraag of ie koffie wil"),
    "simon?":            (150, simon, "simon?, kijkt of simon op sorcsoft ingelogd is"),
    "citaat":            (150, citaat, "citaat, geeft een random regel text die ooit gezegd is"),
    "context":            (150, context, "context <text>, geeft de context waarin iets gezegd is"),
    "wees stil":         (1000, leeg, "wees stil, laat piet z'n kop houden met loze dingen"),
    "stil?":             (1000, leeg, "stil?, probeert piet zich stil te houden?"),
    "praat maar":        (1000, leeg, "praat maar, tegenovergestelde van \"wees stil\""),
    "lees lua":          (1000, leeg, "lees lua, herlees het lua script"),
		"kies":              (100, kies, "kies een willekeurig woord uit de opgegeven lijst"),
    "mep":               (100, mep, ""),
    "geef":              (100, geef, ""),
    "dum":               (0, dum, ""),
    "wiki":		 (500, wiki, "wiki <woord> Freeware encyclopedie"),
    "tel":               (1000, tel, "geef weary's mobielnr"),
    "tijd":		 (0, tijd, "tijd, geeft aan hoe laat het is in Sydney en Amsterdam"),
    "ns":                (500, ns, "ns <vertrekplaats> <aankomstplaats> <tijd>"),
    "trein":                (1200, trein, ""),
    "quote":             (1000, quote, "quote <add> <regel> om iets toe te voegen of quote om iets op te vragen"),
    "onbekend_commando": (0, onbekend_commando, "")};

def parse(param_org, first, magzeg):
  global auth,nick;
  #print ("parse entry:", param_org, first);
  command=string.split(param_org, ' ')[0];
  params=string.join(string.split(param_org, ' ')[1:],' ');


  functie=d["zeg"];
  try:
    functie=d[command];
  except:
    if (first):
      functie=d["onbekend_commando"];
    else:
      params=param_org;

  #print (command, params, int(auth), functie);
  if (int(auth)<functie[0]):
    if (first):
      functie=d["onbekend_commando"];
    else:
      functie=d["zeg"];
      params=param_org;
  
  #print ("parse, jump to:", functie);
  r="";
  if (int(auth)>=0):
    if (functie==d["zeg"]) and (magzeg==False):
      r=params;
    else:
      r=functie[1](params);

  #print ("r = ", r);
  r2=string.split(r, '\n');
  if (len(r2)>15):
    l=str(len(r2));
    r=string.join(r2[:15], '\n')+"\n"+nick+": de rest verzin je zelf maar, 15 van de "+l+" regels vind ik zat\n";
  return r;

#print ("2",nick, auth, channel, msg);
print parse(msg, True, True);



