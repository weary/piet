import os,time,string,re;
import piet;

localtimezone="Europe/Amsterdam";

# maak lijst gescheiden door ,'s, behalve tussen laatste 2 items, waar "en" komt
def make_list(p):
	p=list(p);
	if len(p)==0:
		return "";
	elif len(p)==1:
		return p[0];
	
	prefix=p[:-1];
	postfix=p[-1];
	return string.join(prefix, ", ")+" en "+postfix;

# maak een nederlandse zin van secs. secs moet een tijdsduur weergeven, niet een
# absolute tijd, zie format_localtijd voor absolute tijd, items geeft de precisie
def format_tijdsduur(secs, items=2):
	secs=round(secs);
	if (secs==0):
		return "geen tijd";
	
	tijd=[];
	d=int(secs/86400); secs=secs-d*86400;
	h=int(secs/3600); secs=secs-h*3600;
	m=int(secs/60); secs=secs-m*60;
	s=secs;
	if (d==1):
		tijd.append("een dag");
	elif (d>1 or d<0):
		tijd.append(str(d)+" dagen");
		
	if (h==1):
		tijd.append("een uur");
	elif (h>1 or h<0):
		tijd.append(str(h)+" uren");
		
	if (m==1):
		tijd.append("een minuut");
	elif (m>1 or m<0):
		tijd.append(str(m)+" minuten");
		
	if (s==1):
		tijd.append("een seconde");
	elif (s>1 or m<0):
		tijd.append(str(s)+" secondes");

	tijd=tijd[:items];

	if (len(tijd)==0):
		return "tijd verprutst";

	return make_list(tijd);


# convert tijd-string naar secs t.o.v epoch
def parse_tijd(tijd, tijdzone):
	tijd=string.strip(tijd);
	datesplit=re.match("(\d{1,2})[-/ ](\d{1,2})[-/ ](\d{4})", tijd);
	datum=""; datumformat="";
	if (datesplit!=None):
		datumformat="%d-%m-%Y ";
		datum=datesplit.group(1)+"-"+datesplit.group(2)+"-"+datesplit.group(3)+" ";
		tijd=string.strip(tijd[datesplit.end():]);
			
	try:
		tijd = time.strptime(datum+tijd, datumformat+"%H:%M");
	except:
		tijd = time.strptime(datum+tijd, datumformat+"%H:%M:%S");
		# note, no try/except here, if not parsed here, exception will fall through

	os.environ['TZ']=tijdzone;
	time.tzset();
	if (datum):
		tijd=time.mktime(tijd);
	else:
		lc=time.localtime();
		tijd=(tijd[3]-lc[3])*3600+(tijd[4]-lc[4])*60+(tijd[5]-lc[5])+time.time();
		#if (tijd<0): tijd+=24*3600;
	timezone_reset();
	
	return tijd;


# geef de tijdzone van de gegeven nick. als nick niet bekend is, dan default tijdzone
def tijdzone_nick(naam):
	inp=piet.db('SELECT timezone FROM auth where name="'+naam+'"');
	if (inp==None or len(inp)<=1):
		tz=localtimezone;
	else:
		tz=inp[1][0];
	return tz;


# zet tijdzone terug op standaard
def timezone_reset():
	os.environ['TZ']=localtimezone;
	time.tzset();


# zet de gegeven tijd (secs, in seconden sinds epoch) om in lokale tijd voor de
# gegeven tijdzone in het gegeven formaat. zie tijdzone_nick voor de tijdzone.
def format_localtijd(secs, format="%H:%M", tijdzone=localtimezone):
	os.environ['TZ']=tijdzone;
	time.tzset();
	result=time.strftime(format, time.localtime(secs));
	timezone_reset();
	return result;


