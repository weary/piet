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
  return result

