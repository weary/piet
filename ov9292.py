import urllib,cgi,re,string,time,os;
import pietlib,piet;

ov9292url="http://www.9292mobiel.nl/";

try:
    ovresults; # data structure to store old results
except:
    ovresults={};
    

def parse_ov9292(raw,path):
    form=re.search('<form[^>]*action="([^"]*)"[^>]*>(.*)</form>', raw, re.DOTALL|re.IGNORECASE);
    action=form.group(1);
    form=form.group(2);
    
    n=action.rfind('/');
    if action[0]=='/':
        path=action[1:n+1];
        action=action[n+1:];
    elif n>=0:
        path=path+action[:n+1];
        action=action[n+1:];
        
    q={};
    for i,j in re.findall('<input type="hidden" [^>]*name="([^"]*)" [^>]*value="([^"]*)" [^>]*>', form):
        q[i]=j;
    q["verder"]="Ga verder";
    return action,path,q,form;

def findselectbox(form):
    r=re.findall('<option [^>]*value=["\']([^"\']*)["\'][^>]*>(.*)</option>', form);
    r=[(j,i) for i,j in r];
    return r;

def do_fetch(action, actionpath, q):
    if len(q)>0:
        q="?"+urllib.urlencode(q);
    else:
        q="";
    url=ov9292url+actionpath+action+q;
    raw=pietlib.get_url(url);
    return parse_ov9292(raw, actionpath);

def niet_herkent(channel, what, choice, choices):
  choices.remove(choice);
  str=what+" niet herkend, ik pak "+choice;
  if len(choices)>0:
    str=str+" (en niet "+pietlib.make_list(choices, "of")+")";
  piet.send(channel,str);

def do_station(station, action, actionpath, q, channel):
    # choose "station" (q["typ"]=1 - station, q["typ"]=3 - adres)
    q["typ"]=1;
    action,actionpath,q,form=do_fetch(action, actionpath, q);
    q["v1"]=station;
    action,actionpath,q,form=do_fetch(action, actionpath, q);
    if form.find("Kies treinstation")>=0: # misspelled station, select one
        choices=findselectbox(form);
        q["v1"]=choices[0][1];
        niet_herkent(channel, "station "+station, choices[0][0], [i for i,j in choices]);
        action,actionpath,q,form=do_fetch(action, actionpath, q);
    return action,actionpath,q,form;

def do_plaats(adres, action, actionpath, q, channel):
    match=re.match("([^0-9,]*)([ ]+[0-9]+)?[ ]*,(.*)", adres);
    if not(match):
        raise "kon adres \""+adres+"\" niet parsen";
    straat=match.group(1).strip();
    hasnr=False;
    if match.group(2):
        hasnr=True;
        nr=match.group(2).strip();
    plaats=match.group(3).strip();
    
    # choose adres (q["typ"]=1 - station, q["typ"]=3 - adres)
    q["typ"]=3;
    action,actionpath,q,form=do_fetch(action, actionpath, q);
    q["v1"]=plaats;
    action,actionpath,q,form=do_fetch(action, actionpath, q);
    if form.find("Kies plaats")>=0: # misspelled city
        choices=findselectbox(form);
        q["v1"]=choices[0][1];
        niet_herkent(channel, "plaats "+plaats, choices[0][0], [i for i,j in choices]);
        action,actionpath,q,form=do_fetch(action, actionpath, q);
    
    q["v1"]=straat;
    if hasnr:
        q["v2"]=nr;
    else:
        q["v2"]="";

    action,actionpath,q,form=do_fetch(action, actionpath, q);
    if form.find("Kies straat")>=0: # misspelled street
        choices=findselectbox(form);
        q["v1"]=choices[0][1];
        niet_herkent(channel, "straat "+straat, choices[0][0], [i for i,j in choices]);
        action,actionpath,q,form=do_fetch(action, actionpath, q);
        
    return action,actionpath,q,form;

def ov9292(param,nick,channel):
    print("ov start");
    par=re.match("[ ]*(optie|keuze)?[ ]*([abcABC123])[ ]*$", param)
    if par:
        # probeer oude resultaten op te halen
        nr=par.group(2);
        if nr.isdigit():
            nr=int(nr)-1;
        elif nr>='a' and nr<='z':
            nr=ord(nr)-ord('a');
        else:
            nr=ord(nr)-ord('A');
        
        if not(ovresults.has_key(nick)):
            return "maar ik heb helemaal geen reizen opgeslagen voor jou, "+nick;
        results=ovresults[nick];
        if nr>=len(results):
            return "d'r is vast een resultaat zoekgeraakt ofzo, kan nr "+str(nr+1)+" niet vinden";
        return results[nr];            
   
    print("ov zoektocht");
    # nieuwe zoekopdracht
    tz=pietlib.tijdzone_nick(nick);
    regex=\
    '(["]([^"]*)["]|([^"][^ ]*))[ ]+(["]([^"]*)["]|([^"][^ ]*))[ ]*'+\
    '(vertrek|aankomst)?[ ]*(.*)';
    par=re.match(regex, param);
    if not(par):
        return 'ik snap d\'r geen hout van, parameters moeten zijn: '\
        '"<van>" "<naar>" vertrek|aankomst datum tijd'
    van=par.group(2) or par.group(3);
    naar=par.group(5) or par.group(6);
    vertrek='D';
    if par.group(7) and par.group(7).strip()=="aankomst":
        vertrek='A';
    tijd=time.time();
    tijdstr=par.group(8).strip();
    if len(tijdstr)>0:
        try:
            tijd=pietlib.parse_tijd(tijdstr,tz);
        except:
            return 'De datum+tijd '+tijdstr+' snap ik niet, sorry';
   
    print("ov van \""+van+"\" naar \""+naar+"\" om "+str(tijd));

    # get frontpage
    print("ov 1");
    action,actionpath,q,form=do_fetch("", "", {});

    print("ov 2");
    # get from-radiobuttons
    action,actionpath,q,form=do_fetch(action, actionpath, q);

    print("ov 3");
    if van.find(',')>=0:
        action,actionpath,q,form=do_plaats(van, action, actionpath, q, channel);
    else:
        action,actionpath,q,form=do_station(van, action, actionpath, q, channel);

    print("ov 4");
    if naar.find(',')>=0:
        action,actionpath,q,form=do_plaats(naar, action, actionpath, q, channel);
    else:
        action,actionpath,q,form=do_station(naar, action, actionpath, q, channel);
    
    print("ov 5");
    # tijd/datum
    os.environ['TZ']="Europe/Amsterdam";
    time.tzset();
    tijdstruct=time.localtime(tijd);
    q["d"]=time.strftime("%Y-%m-%d", tijdstruct);
    q["u"]=time.strftime("%H", tijdstruct);
    q["m"]=time.strftime("%M", tijdstruct);
    q["v"]=vertrek; # D=vertrek, A=aankomst
    pietlib.timezone_reset();

    action,actionpath,q,form=do_fetch(action, actionpath, q);

    regex=\
    "<tr><td>(Ver[^&]*)[^<]*<[/]td><td[^>]*>([^<]*)<[/]td><[/]tr>[^<]*"+\
    "<tr><td>([^&]*)[^<]*<[/]td><td[^>]*>([^<]*)<[/]td><[/]tr>[^<]*"+\
    "<tr><td>([^&]*)[^<]*<[/]td><td[^>]*>([^<]*)<[/]td><[/]tr>[^<]*"+\
    "<tr><td>([^&]*)[^<]*<[/]td><td[^>]*>([^<]*)<[/]td><[/]tr>[^<]*"+\
    "<tr><td [^>]*><a (href)=\"([^>]*)\">[^>]*><[/]td><[/]tr>"+\
    "";
    results=re.findall(regex, form, re.DOTALL|re.IGNORECASE);
    print("ov 6 (done, fetching individual results)");
    if len(results)==0:
      piet.send(channel, "9292mobiel site is weer stuk, blijkbaar. ik heb een leeg lijstje gekregen.");

    r=[];
    for i in results:
        piet.send(channel, i[0]+": "+i[1]+", "+i[2]+": "+i[3]+", "+i[4]+": "+i[5]+", "+i[6]+\
        ": "+i[7]+" (zeg \""+piet.nick()+": ov "+("ABCDEF"[len(r)])+"\")");
        qs=i[9];
        url=ov9292url+actionpath+qs.replace("&amp;", "&");
        raw=pietlib.get_url(url);
        res=re.findall(\
        "<tr><td><span class='kop'>([^<]*)<[/]span>"+\
        "<span class='kopn'>([^<]*)<[/]span>"\
        "</td></tr><tr><td class='kopn'>([^<]*)</td></tr>", raw, re.DOTALL|re.IGNORECASE);
        r.append(string.join([string.join(i) for i in res], '\n'));
        print("ov got an individual result");
    ovresults[nick]=r;
    print("ov done\n");
    return "";


