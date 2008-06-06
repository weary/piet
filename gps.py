#!/usr/bin/python
# -*- coding: iso-8859-1 -*-

import string,time,datetime;
from pietlib import get_url;

def gps_coord(regel):
  url="http://maps.google.com/maps?q="
  regel=string.replace(regel," ","+")
  url+=regel
  result=get_url(url)
  if string.find(result,"Your search for") > 0:
    return "Staat niet op de kaart"
  if string.find(result,"Did you mean") > 0:
    x=string.find(result,"Did you mean")
    x=string.find(result,"geocode=",x)+8
    y=string.find(result,"\\",x)
    geocode=result[x:y]
    x=string.find(result,"ref_desc",x)
    x=string.find(result,"x3e",x)+3
    y=string.find(result,"x3c",x)-1
    place=result[x:y]
    geocodes=string.split(geocode,",")
    if float(geocodes[1])>0:
      geocode="N: "
    else:
      geocode="S: "
    geocode+=str(abs(int(float(geocodes[1]))))+"°"
    x=string.find(geocodes[1],".")
    geocode+=str(float("0."+geocodes[1][x+1:])*60)[:6]+"' "
    if float(geocodes[2])>0:
      geocode+="E: "
    else:
      geocode+="W: "
    geocode+=str(abs(int(float(geocodes[2]))))+"°"
    x=string.find(geocodes[2],".")
    geocode+=str(float("0."+geocodes[2][x+1:])*60)[:6]+"'"
    return place+": GPS: "+geocode

  x=string.find(result,"{lat:")+5
  y=string.find(result,",",x)
  lat=result[x:y]
  x=string.find(result,",lng:")+5
  y=string.find(result,"}",x)
  lng=result[x:y]
  result="GPS: "
  lat=float(lat)
  lng=float(lng)
  if lat<0:
    result+="S:"
  else:
    result+="N:"
  result+=" "+str(abs(int(lat)))
  lat=abs(lat)
  minutes=str(60*(lat-int(lat)))
  x=string.find(minutes,".")+4
  if x<6:
    minutes="0"+minutes
  result+="°"+minutes[:6]+"' "
  if lng<0:
    result+="W:"
  else:
    result+="E:"
  result+=" "+str(abs(int(lng)))
  lng=abs(lng)
  minutes=str(60*(lng-int(lng)))
  x=string.find(minutes,".")+4
  if x<6:
    minutes="0"+minutes
  result+="°"+minutes[:6]+"'"
  if string.strip(result)=="GPS: N: 37°03.75' W: 95°40.624'":
    return "Staat niet op de kaart"
  return result

