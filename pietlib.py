import os, time, re, urllib, sys;
sys.path.append(".");
import BeautifulSoup;
import piet;
import calc;

DEFAULTAGENT = "wget/1.1";

def get_url(url, postdata=None, agent=DEFAULTAGENT):
  class PietUrlOpener(urllib.FancyURLopener):
    version = agent;
  
  oldopener = urllib._urlopener;
  urllib._urlopener = PietUrlOpener();
  if not(postdata):
    tmp = urllib.urlopen(url).read(100000);
  else:
    if (type(postdata)==dict):
      postdata = urllib.urlencode(postdata);
    tmp = urllib.urlopen(url, postdata).read(100000);
  urllib._urlopener = oldopener;
  return tmp;


def get_url_soup(url, agent=DEFAULTAGENT):
  return BeautifulSoup.BeautifulSoup(get_url(url, agent=agent));

LOCALTIMEZONE = "Europe/Amsterdam";

# maak lijst gescheiden door ,'s, behalve tussen laatste 2 items, waar "en" komt
def make_list(items, sep="en"):
  items = list(items);
  if not(items):
    return "";
  elif len(items) == 1:
    return items[0];
  
  prefix = items[:-1];
  postfix = items[-1];
  return ", ".join(prefix)+" "+sep+" "+postfix;

# maak een nederlandse zin van secs. secs moet een tijdsduur weergeven, niet
# een absolute tijd, zie format_localtijd voor absolute tijd, items geeft de
# precisie
def format_tijdsduur(secs, items=2):
  secs = int(round(secs));
  if (secs == 0):
    return "geen tijd";
  
  tijd = [];
  (dagen, secs) = divmod(secs, 86400);
  (uren, secs) = divmod(secs, 3600);
  (minuten, secs) = divmod(secs, 60);
  if (dagen == 1):
    tijd.append("een dag");
  elif (dagen>1 or dagen<0):
    tijd.append(str(dagen)+" dagen");
    
  if (uren == 1):
    tijd.append("een uur");
  elif (uren>1 or uren<0):
    tijd.append(str(uren)+" uren");
    
  if (minuten == 1):
    tijd.append("een minuut");
  elif (minuten>1 or minuten<0):
    tijd.append(str(minuten)+" minuten");
    
  if (secs == 1):
    tijd.append("een seconde");
  elif (secs>1 or secs<0):
    tijd.append(str(secs)+" secs");

  tijd = tijd[:items];

  if (len(tijd) == 0):
    return "tijd verprutst";

  return make_list(tijd);

DATEREGEX = \
"(\d{1,2})[-/ ](\d{1,2}|"+"|".join(calc.monthmap.keys())+")[-/ ](\d{4})|"+\
"(vandaag|morgen|overmorgen)";

# convert tijd-string naar secs t.o.v epoch
# als er geen datum gegeven is, en de tijd<nu is, dan wordt er 24 uur bij
# opgeteld
def parse_tijd(tijd, tijdzone):
  def parse_abs_tijd(datesplit):
    try:
      day = int(datesplit.group(1));
      year = int(datesplit.group(3));
      month = int(datesplit.group(2));
    except TypeError:
      try:
        month = calc.monthmap[datesplit.group(2).lower()];
      except KeyError:
        have_date = False;
  
    if have_date:
      datumformat = "%d-%m-%Y ";
      datum = "%s-%s-%s " % (day, month, year);
    return (datumformat, datum);

  def parse_rel_tijd(datesplit):
    os.environ['TZ'] = tijdzone;
    time.tzset();
    t_now = time.time();
    if datesplit.group(4) == "vandaag":
      datum = time.strftime("%d-%m-%Y ", time.localtime(t_now));
      datumformat = "%d-%m-%Y ";
    elif datesplit.group(4) == "morgen":
      datum = time.strftime("%d-%m-%Y ", time.localtime(t_now+24*60*60));
      datumformat = "%d-%m-%Y ";
    elif datesplit.group(4) == "overmorgen":
      datum = time.strftime("%d-%m-%Y ", time.localtime(t_now+2*24*60*60));
      datumformat = "%d-%m-%Y ";
    return (datumformat, datum);

  tijd = tijd.strip();
  datesplit = re.match(DATEREGEX, tijd);
  datum = "";
  datumformat = "";
  have_date = False;
  if datesplit:
    have_date = True;
    assert(datesplit.group(1) or datesplit.group(4));
    if datesplit.group(1):
      datumformat, datum = parse_abs_tijd(datesplit);
    else:
      datumformat, datum = parse_rel_tijd(datesplit);

    if (have_date):
      tijd = tijd[datesplit.end():].strip();

  try:
    tijd = time.strptime(datum+tijd, datumformat+"%H:%M");
  except ValueError:
    tijd = time.strptime(datum+tijd, datumformat+"%H:%M:%S");
    # note, no try/except here, if not parsed here, exception will fall through

  os.environ['TZ'] = tijdzone;
  time.tzset();
  if (datum):
    tijd = time.mktime(tijd);
  else:
    loctime = time.localtime();
    tijd = (
        (tijd[3]-loctime[3])*3600+
        (tijd[4]-loctime[4])*60+
        (tijd[5]-loctime[5])+
        time.time());
    #if (tijd<0): tijd+=24*3600;
  timezone_reset();

  if not(have_date):
    rel_tijd = tijd-time.time();
    if (rel_tijd<0 and rel_tijd>-24*3600):
      tijd += 24*3600;

  return round(tijd);


# geef de tijdzone van de gegeven nick. als nick niet bekend is, dan default
# tijdzone
def tijdzone_nick(naam):
  inp = piet.db('SELECT timezone FROM auth where name="'+naam+'"');
  if (not(inp) or len(inp)<=1):
    tzone = LOCALTIMEZONE;
  else:
    tzone = inp[1][0];
  return tzone;


# zet tijdzone terug op standaard
def timezone_reset():
  os.environ['TZ'] = LOCALTIMEZONE;
  time.tzset();


# zet de gegeven tijd (secs, in seconden sinds epoch) om in lokale tijd voor de
# gegeven tijdzone in een handig formaat. zie tijdzone_nick voor de tijdzone.
def format_localtijd(secs, tijdzone=LOCALTIMEZONE):
  os.environ['TZ'] = tijdzone;
  time.tzset();
  now = time.localtime();
  morgen = time.localtime(time.time()+24*3600);
  overmorgen = time.localtime(time.time()+48*3600);
  loc=time.localtime(secs);
  if (now[0] != loc[0]):
    result = time.strftime("%d-%m-%Y %H:%M", loc);
  elif (morgen[:3] == loc[:3]):
    result = time.strftime("morgen, %H:%M", loc);
  elif (overmorgen[:3] == loc[:3]):
    result = time.strftime("overmorgen, %H:%M", loc);
  elif (now[:3] != loc[:3]):
    result = time.strftime("%d %b %H:%M", loc);
  else:
    result = time.strftime("%H:%M", loc);
  timezone_reset();
  return result;


