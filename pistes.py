#!/usr/bin/python

#
# functie: pistes
# omschrijving: zoekt op hoeveel liften en pistes open zijn
# syntax: pistes [<lokatie> ...]
# versie: 2005-12-19
# wijzigingen:
#   2005-12-19
#    - soelden gefixd
#    - les2alpes toegevoegd
#    - winterberg/skiliftkarussell toegevoegd
#    - interface aangepast zodat lokaties spaties kunnen bevatten
#   2005-12-18
#    - initiele versie met winterberg en soelden
#

import urllib
from sets import Set



def cmd_pistes(cmd):
  overzicht = [ \
    pistes_les2alpes, \
    pistes_winterberg_skiliftkarussell, \
    pistes_soelden ]

  aliases = { \
    "duitsland":[pistes_winterberg,pistes_winterberg_skiliftkarussell], \
    "winterberg":[pistes_winterberg,pistes_winterberg_skiliftkarussell], \
    "skiliftkarussell":[pistes_winterberg_skiliftkarussell], \
    \
    "frankrijk":[pistes_les2alpes], \
    "2 alpe":[pistes_les2alpes], \
    "deux alpes":[pistes_les2alpes], \
    "les2alpes":[pistes_les2alpes], \
    "twee alpen":[pistes_les2alpes], \
    \
    "nederland":[pistes_enschede], \
    "enschede":[pistes_enschede], \
    \
    "oostenrijk":[pistes_soelden], \
    "soelden":[pistes_soelden], \
    "solden":[pistes_soelden], \
    \
    "overal":overzicht, \
    "overzicht":overzicht }

  for teken in ",.;:\"'`!?()":
    cmd = cmd.replace(teken,"")

  pistes = Set()
  if (cmd == ""):
    for fs in overzicht:
      pistes.add(fs)
  else:
    for naam in aliases.keys():
      if (naam in cmd):
        pistes.union_update(aliases[naam])
    if (len(pistes) == 0):
      return cmd+"? waar precies?"
  
  zegdit = []
  for f in pistes:
    zegdit.append(f())

  return "\n".join(zegdit)



def pistes_enschede():
  return "enschede: probeer eens de ijsbaan"



def pistes_les2alpes():
  keys = [ "Lift  : </b>" , \
    "IMG/ico_p_vert.gif\" align=\"center\" />\x0d\n", \
    "IMG/ico_p_bleu.gif\" align=\"center\" />\x0d\n", \
    "IMG/ico_p_rouge.gif\" align=\"center\" />\x0d\n", \
    "IMG/ico_p_noir.gif\" align=\"center\" />\x0d\n" ]
  i_liften, i_groen, i_blauw, i_rood, i_zwart = range(5)

  try:
    sock = urllib.urlopen("http://www.les2alpes.com/asources/meteo/meteoaff.asp?lg=uk")

    try:
      html = sock.read()

      waarden = []
      for i in range(5):
        p = html.index(keys[i]) + len(keys[i])
        waarden.append ([ int(html[p:html.index("/",p)]) , \
          int(html[html.index("/",p)+1:html.index("<",p)]) ])

      pistes_aan = 0
      pistes_totaal = 0
      for i in range(i_groen,i_zwart+1):
        pistes_aan += waarden[i][0]
        pistes_totaal += waarden[i][1]

      msg = "les2alpes: %d des %d ascenceurs et %d des %d pistes sont utilee" % (waarden[i_liften][0] , waarden[i_liften][1], pistes_aan, pistes_totaal)

    except ValueError:
      msg="ACTION kan les2alpes.com niet meer lezen"

    except IOError:
      msg="les2alpes.com is onbetrouwbaar"

    sock.close()
    return msg

  except IOError:
    return "ACTION kan les2alpes niet vinden"



def pistes_soelden():
  try:
    sock = urllib.urlopen("http://www.soelden.com/main/EN/WI/WetterSchnee/Heute/index,method=main.html")

    try:
      html = sock.read()

      p_liftentabel = html.index("LIFTS IN OPERATION")
      p_pistetabel = html.index("OPEN SKI RUNS")
      p_basetabel = html.index("</table",p_pistetabel)

      liften_aan = html.count("<td class=\"text10\" valign=\"top\">Open</td>", \
        p_liftentabel,p_pistetabel)
      pistes_aan = html.count("<td class=\"text10\" valign=\"top\">Open</td>", \
        p_pistetabel,p_basetabel)

      liften_totaal = html.count("<tr ",p_liftentabel,p_pistetabel)
      pistes_totaal = html.count("<tr ",p_pistetabel,p_basetabel)

      msg = "soelden: %d der %d liften und %d der %d pisten sind in betrieb" % (liften_aan , liften_totaal, pistes_aan, pistes_totaal)

    except ValueError:
      msg="ACTION kan soelden.com niet meer lezen"

    except IOError:
      msg="soelden.com is onbetrouwbaar"

    sock.close()
    return msg

  except IOError:
    return "ACTION kan soelden niet vinden"



def pistes_winterberg():
  try:
    sock = urllib.urlopen("http://www2.winterberg.de/de/snow-fun/schneehoehen_alpin.php")

    try:
      html = sock.read()

      flocken_an = html.count("icon_flocke_an.gif")
      flocken_aus = html.count("icon_flocke_aus.gif")

      msg = "winterberg: %d der %d skigebiete sind beskibar" \
        % (flocken_an , flocken_an+flocken_aus)

    except IOError:
      msg="winterberg.de is onbetrouwbaar"

    sock.close()
    return msg

  except IOError:
    return "ACTION kann winterberg nicht finden"



def pistes_winterberg_skiliftkarussell():
  try:
    sock = urllib.urlopen("http://univers.skiliftkarussell.de/schnee-info.htm")

    try:
      html = sock.read()

      flocken_an = html.count("ein.gif")
      flocken_aus = html.count("aus.gif")

      msg = "winterberg/skiliftkarussell: %d der %d liften sind in betrieb" \
        % (flocken_an , flocken_an+flocken_aus)

    except IOError:
      msg="skiliftkarussell.de is onbetrouwbaar"

    sock.close()
    return msg

  except IOError:
    return "ACTION kann skiliftkarussell winterberg nicht finden"



#import sys
#args = sys.argv
#del (args[0])
#print cmd_pistes(' '.join(args))
