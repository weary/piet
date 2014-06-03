import os, time, re, urllib, sys, datetime, calendar
sys.path.append(".")
import BeautifulSoup
import traceback
import piet
import calc

DEFAULTAGENT = "wget/1.1";

class logstream(object):
	def __init__(self, s):
		self.stream = s

	def write(self, text):
		piet.log(self.stream + text)

if not 'debugpiet' in piet.__dict__:
	sys.stdout = logstream("")

class piet_exception(Exception):
  """ an exception that will be send to the channel. should be used to signal
  an error condition with a message for the user """
  _text = None

  def __init__(self, text_):
    Exception.__init__(self)
    self._text = text_
    traceback.print_exc();

  def __str__(self):
    return self._text


def get_url(url, postdata=None, agent=DEFAULTAGENT, incookies=[], outcookies=[], maxsize=100000, headers=[]):
  class PietUrlOpener(urllib.FancyURLopener):
    version = agent
  
  # incookies should be ['label=value', 'label2=value2']
  # outcookies will be appended with ['label=value; path=/', 'label2=value2; path=/; ..']
  
  oldopener = urllib._urlopener
  urllib._urlopener = PietUrlOpener()
  for name,val in headers:
    urllib._urlopener.addheader(name, val)
  if incookies:
    urllib._urlopener.addheader('Cookie', '; '.join(incookies))
  try:
    if not(postdata):
      urlobj = urllib.urlopen(url)
    else:
      if (type(postdata)==dict):
        postdata = urllib.urlencode(postdata)
      urlobj = urllib.urlopen(url, postdata)
    tmp = urlobj.read(maxsize)
    outcookies.extend(urlobj.info().getheaders('set-cookie'))
  except:
    raise piet_exception("die stomme site reageert niet, andere keer misschien")
  urllib._urlopener = oldopener
  return tmp


def get_url_soup(url, postdata=None, agent=DEFAULTAGENT):
  return BeautifulSoup.BeautifulSoup(get_url(url, postdata=postdata, agent=agent));

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

# if a word is following a number, and it contains 1 or 2 hashes (#), it is changed to the correct plural
# hash-syntax:
#  1 hash: vrouw#en -> single 'vrouw', plural 'vrouwen'
#  2 hashes: lo#op#pen -> single 'loop', plural 'lopen'
def meervoud(line):
	words = line.split(' ')
	for i in xrange(1,len(words)):
		if '#' in words[i] and words[i-1].isalnum():
			parts = words[i].split('#')
			print repr(parts)
			if (len(parts)!=2 and len(parts)!=3) or not words[i-1].isdigit():
				continue
			val = int(words[i-1])
			if val == 1 and len(parts)==2:
				words[i] = parts[0]
			elif val == 1:
				words[i] = parts[0]+parts[1]
			elif len(parts)==2:
				words[i] = parts[0]+parts[1]
			else:
				words[i] = parts[0]+parts[2]
	return ' '.join(words)


# maak een nederlandse zin van secs. secs moet een tijdsduur weergeven, niet
# een absolute tijd, zie format_localtijd voor absolute tijd, items geeft de
# precisie
def format_tijdsduur(secs, items=2):
  assert(items > 0)

  secs = int(round(float(secs)));

  if secs == 0:
    return "nu"

  sign = secs < 0
  if sign:
    secs = -secs

  units = ((365*86400, "jaren", "jaar"),
          (7*86400, "weken", "week"),
          (86400, "dagen", "dag"),
          (3600, "uren", "uur"),
          (60, "minuten", "minuut"),
          (1, "secs", "seconde"))

  out = []
  for multiply, manyword, oneword in units:
    if secs >= multiply:
      amount, secs = divmod(secs, multiply)
      out.append([amount, multiply, manyword, oneword])
      if secs == 0:
        break

  if len(out) > items:
    if out[items][0] >= (out[items-1][1]/2): # round up
      out[items-1][0] += 1
    out = out[:items]

    # fix overflow caused by rounding
    for i in xrange(items-1, 0, -1):
      if out[i][0] >= out[i][1]:
        out[i-1][0] += 1

  words = lambda x: x[0] == 1 and ("een %s" % x[3]) or ("%s %s" % (x[0], x[2]))
  out = pietlib.make_list(words(x) for x in out)
  if sign:
    return "min " + out
  return out


# copy-paste from http://docs.python.org/lib/datetime-tzinfo.html
# needed to work with datetime library and timezones
class LocalTimezone(datetime.tzinfo):
	def __init__(self):
		self.STDOFFSET = datetime.timedelta(seconds = - time.timezone)
		if time.daylight:
			self.DSTOFFSET = datetime.timedelta(seconds = - time.altzone)
		else:
			self.DSTOFFSET = self.STDOFFSET
		self.DSTDIFF = self.DSTOFFSET - self.STDOFFSET
		self.ZERO = datetime.timedelta(0)
	def utcoffset(self, dt):
		if self._isdst(dt):
			return self.DSTOFFSET
		else:
			return self.STDOFFSET
	def dst(self, dt):
		if self._isdst(dt):
			return self.DSTDIFF
		else:
			return self.ZERO
	def tzname(self, dt):
		return time.tzname[self._isdst(dt)]
	def _isdst(self, dt):
		tt = (dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second, dt.weekday(), 0, -1)
		stamp = time.mktime(tt)
		tt = time.localtime(stamp)
		return tt.tm_isdst > 0

def to_float(x):
	return float(x.replace(",","."))

def nogroups(x):
	return re.sub("[(]([^?])", "(?:\\1", x)

DATEREGEX = \
	"(\d{1,2})[-/ ](\d{1,2}|"+"|".join(calc.monthmap.keys())+")[-/ ](\d{4})|" \
	"(vandaag|morgen|overmorgen)"

# only absolute time is matched
ABSTIMEREGEX = "(\d{1,2}):(\d{2})(?:[:](\d{2}))?(?:\s*uur)?"

unitaliasses={
	"j": 365*24*3600,
	"jaar": 365*24*3600,
	"jaren": 365*24*3600,
	"w": 7*24*3600,
	"week": 7*24*3600,
	"weken": 7*24*3600,
	"d": 24*3600,
	"dag": 24*3600,
	"dagen": 24*3600,
	"u": 3600,
	"uur": 3600,
	"uren": 3600,
	"h": 3600,
	"m": 60,
	"min": 60,
	"minuten": 60,
	"s": 1,
	"sec": 1,
	"secondes": 1,
	"seconden": 1}

# match one element from "5 jaren 10 dagen"
RELTIMEELEM = "([\d,.]+)\s*(%s)" % '|'.join([u+"(?:\\b|\\Z)" for u in unitaliasses.keys()])

RELTIMEREGEX = "%s(?:[\s]+%s)*" % (nogroups(RELTIMEELEM), nogroups(RELTIMEELEM))

TIMEREGEX = "(%s)|(%s)" % (nogroups(ABSTIMEREGEX), nogroups(RELTIMEREGEX))
DATETIMEREGEX = "(?:(%s)\s+(%s))|(?:(%s)\s+(%s))|(%s)|(%s)" % (
		nogroups(DATEREGEX), nogroups(TIMEREGEX),
		nogroups(TIMEREGEX), nogroups(DATEREGEX),
		nogroups(TIMEREGEX), nogroups(DATEREGEX))

# convert tijd-string naar secs t.o.v epoch
# als er geen datum gegeven is, en de tijd<nu is, dan wordt er 24 uur bij
# opgeteld
# returns tuple (time-since-epoch, remainder-of-string)
def parse_tijd(input, tijdzone):
	input = input.strip()
	os.environ['TZ'] = tijdzone
	time.tzset()
	try:
		tz = LocalTimezone()
		now = datetime.datetime.now(tz)

		fullmatch = re.match(DATETIMEREGEX, input, re.IGNORECASE)
		if not(fullmatch):
			raise piet_exception("geen datum/tijd gevonden")
		remainder = input[fullmatch.end():].strip()

		# either date-time or time-date
		datum = fullmatch.group(1) or fullmatch.group(4) or fullmatch.group(6)
		tijd = fullmatch.group(2) or fullmatch.group(3) or fullmatch.group(5)
		#print "datum", repr(datum)
		#print "tijd", repr(tijd)

		the_moment = now

		if datum:
			if datum == "vandaag":
				pass
			elif datum == "morgen":
				the_moment = the_moment + datetime.timedelta(days=1)
			elif datum == "overmorgen":
				the_moment = the_moment + datetime.timedelta(days=2)
			else: # absolute date
				d = re.match(DATEREGEX, datum)
				assert(d and not(d.group(4)))
				day = int(d.group(1))
				year = int(d.group(3))
				month = 0
				try:
					month = int(d.group(2))
				except ValueError:
					try:
						month = calc.monthmap[d.group(2).lower()]
					except KeyError:
						raise piet_exception("onbekende maand: "+repr(d.group(2)))
				d = datetime.date(year, month, day)
				the_moment = datetime.datetime.combine(d, the_moment.time())
			#print "datum", repr(datum), "geparsed naar", the_moment.date()

		if tijd:
			t = re.match(TIMEREGEX, tijd)
			assert(t and (t.group(1) or t.group(2)))
			if t.group(1): # abs time
				t = re.match(ABSTIMEREGEX, t.group(1))
				assert(t)
				uur = int(t.group(1))
				min = int(t.group(2))
				sec = int(t.group(3) or 0)
				t = datetime.time(uur, min, sec, tzinfo=tz)
				the_moment = datetime.datetime.combine(the_moment.date(), t)
			else:
				lt = re.findall(nogroups(RELTIMEELEM), tijd)
				lt = [ re.match(RELTIMEELEM, i).groups() for i in lt ]
				lt = [ to_float(t)*unitaliasses[u] for t,u in lt ]
				the_moment = the_moment + datetime.timedelta(seconds = sum(lt))

			#print "het is nu", time.time()
			#print "tijd", repr(tijd), "geparsed naar", the_moment.time()
		if not(datum) and the_moment<now and the_moment+datetime.timedelta(days=1)>now:
			the_moment = the_moment + datetime.timedelta(days=1)
		
		#print the_moment
		#print "result:",repr(the_moment.utctimetuple())
		#print "result:",calendar.timegm(the_moment.utctimetuple())
		return (calendar.timegm(the_moment.utctimetuple()), remainder)
	finally:
		timezone_reset()


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


