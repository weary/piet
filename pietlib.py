import os,time,string,re,traceback,urllib,BeautifulSoup;
import piet;
import calc;

defaultagent = "wget/1.1";

def get_url(url, postdata={}, agent=defaultagent):
	class pieturlopener(urllib.FancyURLopener):
		version = agent;
	
	oldopener=urllib._urlopener;
	urllib._urlopener = pieturlopener();
	if (len(postdata)==0):
		a=urllib.urlopen(url).read();
	else:
		if (type(postdata)==dict):
			postdata=urllib.urlencode(postdata);
		a=urllib.urlopen(url,postdata).read();
	urllib._urlopener = oldopener;
	return a;


def get_url_soup(url, agent=defaultagent):
	return BeautifulSoup.BeautifulSoup(get_url(url,{},agent));

localtimezone="Europe/Amsterdam";

# maak lijst gescheiden door ,'s, behalve tussen laatste 2 items, waar "en" komt
def make_list(p, sep="en"):
	p=list(p);
	if len(p)==0:
		return "";
	elif len(p)==1:
		return p[0];
	
	prefix=p[:-1];
	postfix=p[-1];
	return string.join(prefix, ", ")+" "+sep+" "+postfix;

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

dateregex=\
"(\d{1,2})[-/ ](\d{1,2}|"+string.join(calc.monthmap.keys(),'|')+")[-/ ](\d{4})|"+\
"(vandaag|morgen|overmorgen)";

# convert tijd-string naar secs t.o.v epoch
# als er geen datum gegeven is, en de tijd<nu is, dan wordt er 24 uur bij opgeteld
def parse_tijd(tijd, tijdzone):
	tijd=string.strip(tijd);
	datesplit=re.match(dateregex, tijd);
	datum=""; datumformat="";
	have_date=False;
	if (datesplit!=None):
		have_date=True;
		if datesplit.group(1):
			try:
				day=int(datesplit.group(1));
				year=int(datesplit.group(3));
				month=int(datesplit.group(2));
			except:
				try:
					month=calc.monthmap[datesplit.group(2).lower()];
				except:
					have_date=False;
		
			if (have_date):
				datumformat="%d-%m-%Y ";
				datum=str(day)+"-"+str(month)+"-"+str(year)+" ";

		elif datesplit.group(4):
			os.environ['TZ']=tijdzone;
			time.tzset();
			t=time.time();
			if datesplit.group(4)=="vandaag":
				datum=time.strftime("%d-%m-%Y ", time.localtime(t));
				datumformat="%d-%m-%Y ";
			elif datesplit.group(4)=="morgen":
				datum=time.strftime("%d-%m-%Y ", time.localtime(t+24*60*60));
				datumformat="%d-%m-%Y ";
			elif datesplit.group(4)=="overmorgen":
				datum=time.strftime("%d-%m-%Y ", time.localtime(t+2*24*60*60));
				datumformat="%d-%m-%Y ";
		else:
			raise("regex and if-statements don't agree");

		if (have_date):
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

	if not(have_date):
		rel_tijd=tijd-time.time();
		if (rel_tijd<0 and rel_tijd>-24*3600):
			tijd+=24*3600;

	return round(tijd);


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
# gegeven tijdzone in een handig formaat. zie tijdzone_nick voor de tijdzone.
def format_localtijd(secs, tijdzone=localtimezone):
	os.environ['TZ']=tijdzone;
	time.tzset();
	now=time.localtime();
	morgen=time.localtime(time.time()+24*3600);
	overmorgen=time.localtime(time.time()+48*3600);
	loc=time.localtime(secs);
	if (now[0]!=loc[0]):
		result=time.strftime("%d-%m-%Y %H:%M", loc);
	elif (morgen[:3]==loc[:3]):
		result=time.strftime("morgen, %H:%M", loc);
	elif (overmorgen[:3]==loc[:3]):
		result=time.strftime("overmorgen, %H:%M", loc);
	elif (now[:3]!=loc[:3]):
		result=time.strftime("%d %b %H:%M", loc);
	else:
		result=time.strftime("%H:%M", loc);
	timezone_reset();
	return result;


