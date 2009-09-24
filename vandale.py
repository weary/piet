import urllib,string

def LookUp(word):
  def CutHTMLTags(s):
    t=0
    result=""
    for x in s:
      if x=="<":
        t+=1
      elif x==">":
        t-=1
      elif t==0:
        if (ord(x)<128):
          result+=x
    return result


  page=urllib.urlopen("http://www.vandale.nl/vandale/opzoeken/woordenboek/?zoekwoord="+word).read()
  s=string.find(page,"pnn4web_b")
  
  if s < 0:
    return word+" niet gevonden"
  result=""
  while s>0:
    s=string.find(page,"<div",s)
    e=string.find(page,"\n",s)

    result+=CutHTMLTags(page[s:e])+"\n"
    s=string.find(page,"pnn4web_b",s)

  return string.strip(result)
