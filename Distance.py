#!/usr/bin/python
# -*- coding: iso-8859-1 -*-

import string,sys,os;

def urlencode(arg):
  arg=string.replace(arg,":","%3A")
  arg=string.replace(arg," ","+")
  return arg

def Distance(args):
  args=string.lower(args)
  args=string.replace(args,"nederlands","netherlands")
# Process arguments
  args=string.split(args,"\"")
  if len(args)%2!=1:
    return "Missing closing \""
  if (len(args)==1):
    args=string.split(args[0]," ")[:2]
  else:
    newargs=[]
    for x in args:
      if x!="":
        newargs+=[x]
    args=newargs[:2]
  args[0]=string.strip(args[0])
  args[1]=string.strip(args[1])
  vanplaats=""
  naarplaats=""
# Enrich list by very important places
  places=[("hilversum","52:13N 5:10E","Hilversum, Netherlands"),("reduzum","53:6N 5:46E","Reduzum, Fryslân"),("cairns","16:51S 145:43E","Cairns, Australia"),("ten boer","53:16N 6:41E","Ten Boer, Netherlands"),("loppersum","53:19N 6:44E","Loppersum, Netherlands"),("leeuwarden","53:11N 5:47E","Leeuwarden, Fryslân"),("groningen","53:13N 6:34E","Groningen, Netherlands"),("enschede","52:13N 6:53E","Enschede, Netherlands"),("hengelo","52:15N 6:47E","Hengelo (ov), Netherlands"),("utrecht","52:5N 5:6E","Utrecht, Netherlands"),("rotterdam","51:93N 4.48E","Rotterdam, Netherlands"),("den haag","52:08N 4:28E","Den Haag, Netherlands"),("'s gravenhage","52:08N 4:28E","Den Haag, Netherlands"),("eindhoven","51:44N 5:47E","Eindhoven, Netherlands"),("tilburg","51:57N 5:07E","Tilburg, Netherlands"),("almere","52:36N 5:17E","Almere, Netherlands"),("breda","51:58N 4:77E","Breda, Netherlands"),("nijmegen","51:84N 5:85E","Nijmegen Netherlands"),("apeldoorn","52:22N 5:96E","Apeldoorn, Netherlands"),("haarlem","52:39N 4:62E","Haarlem, Netherlands"),("arnhem","51.99N 5:91E","Arnhem, Netherlands"),("zaanstad","52:45N 4:82E","Zaanstad, Netherlands"),("den bosch","51:70N 5:31E","Den Bosch, Netherlands"),("amersfoort","52:16N 5:38E","Amersfoort, Netherlands"),("haarlemmermeer","52:30N 4:70E","Haarlemmermeer, Netherlands"),("maastricht","50:85N 5:69E","Maastricht, Netherlands"),("dordrecht","51:80N 4:67E","Dordrect, Netherlands"),("coevorden","52.40N 06.44E","Coevorden, Netherlands"),("cuijk","51.44N 05.50E","Cuijk, Netherlands"),("delft","52.01N 04.22E","Delft, Netherlands"),("delfziji","53.20N 06.55E","Delfziji, Netherlands"),("deurne","51.27N 05.49E","Deurne, Netherlands"),("deventer","52.15N 06.10E","Deventer, Netherlands"),("doesburg","52.01N 06.09E","Doesburg, Netherlands"),("doetinchem","51.59N 06.18E","Doetinchem, Netherlands"),("dokkum","53.20N 05.59E","Dokkum, Netherlands"),("dollard","53.20N 07.10E","Dollard, Netherlands"),("dordrecht","51.48N 04.39E","Dordrecht, Netherlands"),("drachten","53.07N 06.05E","Drachten, Netherlands"),("drenthe","52.52N 06.40E","Drenthe, Netherlands"),("dronten","52.32N 05.43E","Dronten, Netherlands"),("edam","52.31N 05.03E","Edam, Netherlands"),("ede","52.04N 05.40E","Ede, Netherlands"),("eindhoven","51.26N 05.28E","Eindhoven, Netherlands"),("emmeloord","52.44N 05.46E","Emmeloord, Netherlands"),("emmen","52.48N 06.57E","Emmen, Netherlands"),("enkhuizen","52.42N 05.17E","Enkhuizen, Netherlands"),("epe","52.21N 05.59E","Epe, Netherlands"),("ermelo","52.18N 05.35E","Ermelo, Netherlands"),("europoort","51.57N 04.10E","Europoort, Netherlands"),("flevoland","52.30N 05.30E","Flevoland, Netherlands"),("flushing","51.26N 03.34E","Flushing/Vlissingen, Netherlands"),("franeker","53.12N 05.33E","Franeker, Netherlands"),("gelderland","52.05N 06.10E","Gelderland, Netherlands"),("geldrop","51.25N 05.32E","Geldrop, Netherlands"),("geleen","50.57N 05.49E","Geleen, Netherlands"),("goeree","51.50N 04.00E","Goeree, Netherlands"),("goes","51.30N 03.55E","Goes, Netherlands"),("gorinchem","51.50N 04.59E","Gorinchem, Netherlands"),("gouda","52.01N 04.42E","Gouda, Netherlands"),("grouw","53.05N 05.51E","Grouw, Netherlands"),("haaksbergen","52.09N 06.45E","Haaksbergen, Netherlands"),("haarlem","52.23N 04.39E","Haarlem, Netherlands"),("hardenberg","52.34N 06.37E","Hardenberg, Netherlands"),("harderwijk","52.21N 05.38E","Harderwijk, Netherlands"),("harlingen","53.11N 05.25E","Harlingen, Netherlands"),("heerde","52.24N 06.02E","Heerde, Netherlands"),("heerenveen","52.57N 05.55E","Heerenveen, Netherlands"),("heerhugowaard","52.40N 04.51E","Heerhugowaard, Netherlands"),("heerlen","50.55N 05.58E","Heerlen, Netherlands"),("hellevoetsluis","51.50N 04.08E","Hellevoetsluis, Netherlands"),("helmond","51.29N 05.41E","Helmond, Netherlands"),("hertoenbosch's","51.42N 05.17E","Hertoenbosch's, Netherlands"),("hillegom","52.18N 04.35E","Hillegom, Netherlands"),("Hoek van Holland","52.00N 04.07E","Hoek van Holland, Netherlands"),("holwerd","53.22N 05.54E","Holwerd, Netherlands"),("hoogeveen","52.44N 06.28E","Hoogeveen, Netherlands"),("hoogezand-sappemeer","53.09N 06.45E","Hoogezand-sappemeer, Netherlands"),("hoorn","52.38N 05.04E","Hoorn, Netherlands"),("hulst","51.17N 04.02E","Hulst, Netherlands"),("IJmuiden","52.28N 52.28N 04.35E","IJmuiden, Netherlands"),("kampen","52.33N 05.53E","Kampen, Netherlands"),("katwijk","52.12N 04.24E","Katwijk, Netherlands"),("kerkrade","50.53N 06.04E","Kerkrade, Netherlands"),("klazienaveen","52.44N 0.00E","Klazienaveen, Netherlands"),("kollum","53.17N 06.10E","Kollum, Netherlands"),("leek","53.10N 06.24E","Leek, Netherlands"),("leiden","52.09N 04.30E","Leiden, Netherlands"),("lelystad","52.30N 05.25E","Lelystad, Netherlands"),("lemmer","52.51N 05.43E","Lemmer, Netherlands"),("lochem","52.09N 06.26E","Lochem, Netherlands"),("medemblik","52.46N 05.08E","Medemblik, Netherlands"),("meppel","52.42N 06.12E","Meppel, Netherlands"),("middelburg","51.30N 03.36E","Middelburg, Netherlands"),("nijkerk","51.50N 05.52E","Nijkerk, Netherlands"),("nijverdal","52.22N 06.28E","Nijverdal, Netherlands"),("noordwijk","52.14N 04.26E","Noordwijk, Netherlands"),("oldenzaal","52.19N 06.53E","Oldenzaal, Netherlands"),("ommen","52.31N 06.26E","Ommen, Netherlands"),("oosterhout","51.39N 04.47E","Oosterhout, Netherlands"),("oosterwolde","53.0N 06.17E","Oosterwolde, Netherlands"),("oss","51.46N 05.32E","Oss, Netherlands"),("ouddorp","51.50N 3.57E","Ouddorp, Netherlands"),("purmerend","52.32N 04.58E","Purmerend, Netherlands"),("raalte","52.23N 06.16E","Raalte, Netherlands"),("roermond","51.12N 6.0E","Roermond, Netherlands"),("roosendaal","51.32N 4.29E","Roosendaal, Netherlands"),("rottumeroog","53.33N 6.34E","Rottumeroog, Netherlands"),("rottweil","53.33N 6.34E","Rottweil, Netherlands"),("schagen","52.49N 4.48E","Schagen, Netherlands"),("schiedam","51.55N 4.25E","Schiedam, Netherlands"),("schouwen","51.43N 3.45E","Schouwen, Netherlands"),("sittard","51.0N 5.52E","Sittard, Netherlands"),("sluis","51.18N 3.23E","Sluis, Netherlands"),("sneek","53.2N 5.40E","Sneek, Fryslân"),("soest","52.9N 5.19E","Soest, Netherlands"),("terschelling","53.25N 5.20E","Terschelling, Netherlands"),("texel","53.5N 4.50E","Texel, Netherlands"),("tiel","51.53N 5.26E","Tiel, Netherlands"),("tilburg","51.31N 5.6E","Tilburg, Netherlands"),("uden","51.40N 5.37E","Uden, Netherlands"),("valkenswaard","51.21N 5.29E","Valkenswaard, Netherlands"),("vechte","52.34N 6.6E","Vechte, Netherlands"),("veendam","52.2N 5.34E","Veendam, Netherlands"),("venlo","51.22N 6.11E","Venlo, Netherlands"),("venray","51.31N 6.0E","Venray, Netherlands"),("vlieland","53.16N 4.55E","Vlieland, Netherlands"),("vlissingen","51.26N 3.34E","Vlissingen, Netherlands"),("walcheren","51.30N 3.35E","Walcheren, Netherlands"),("weert","51.15N 5.43E","Weert, Netherlands"),("west-terscheling","53.22N 5.13E","West-Terscheling, Netherlands"),("wolvega","52.52N 6.0E","Wolvega, Netherlands"),("workum","52.59N 5.26E","Workum, Netherlands"),("zaanstad","52.27N 4.50E","Zaanstad, Netherlands"),("zwolle","52.31N 6.6E","Zwolle, Netherlands")]

  for (x,y,z) in places:
    if args[0]==x:
      args[0]=urlencode(y)
      vanplaats=z
    if args[1]==x:
      args[1]=urlencode(y)
      naarplaats=z

  url="http://www.indo.com/cgi-bin/dist?place1="+args[0]+"&place2="+args[1]
  inp,outp,stderr = os.popen3("wget -O - -q \""+url+"\"");
  result=outp.read()
  inp.close()
  stderr.close()
  outp.close()

  notfound=string.find(result,"Sorry, our database")
  if notfound>0:
    x=string.find(result,"\"",notfound)+1
    y=string.find(result,"\"",x)
    return result[x:y]+" staat niet op de kaart"

  clarify=string.find(result,"Please clarify")
  while clarify>0:

    x=string.find(result,"Please choose",clarify)
    x=string.find(result,"HREF",x)+6
    y=string.find(result,"\">",x)
    url="http://www.indo.com"+result[x:y]
    inp,outp,stderr = os.popen3("wget -O - -q \""+url+"\"");
    result=outp.read()
    inp.close()
    stderr.close()
    outp.close()
    clarify=string.find(result,"Please clarify")

  x=string.find(result,"crow flies:")+16
  x=string.rfind(result[:x]," between ")+16
  y=string.find(result," and ",x)


  if vanplaats=="":
    vanplaats=result[x:y]
  x=string.find(result," as",y)
  if naarplaats=="":
    naarplaats=result[y+5:x]
  x=string.find(result,"miles",x)
  x=string.find(result,"(",x)+1
  y=string.find(result,")",x)
  result=string.replace(string.strip(result[x:y]+" van "+vanplaats+" naar "+naarplaats+" (zoals de kraai vliegt)"),"Netherlands","Nederland")
  result=string.split(result,"\n")
  for x in range(len(result)):
    result[x]=string.strip(result[x])
  result=string.join(result," ")
  result=string.replace(result,"<STRONG>","")
  result=string.replace(result,"</STRONG>","")
  result=string.replace(result,">","")
  return result

