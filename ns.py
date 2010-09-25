import re, urllib, time, pietlib, piet, os, sys
import BeautifulSoup

debugpiet = 'debugpiet' in piet.__dict__


class StationsNamen:
	# class that can translatie station-names to station-accroniems and back
	# if csv-file 'stationsnamen.txt' exists, use that, otherwise fetch from net on creation

	stations = None # kort -> lang
	stations_inv = None # lang -> kort

	def __init__(self):
		if os.path.exists("stationnamen.txt"):
			lines = open('stationnamen.txt').read().split('\n')
			self.stations = dict(l.split(',',1) for l in lines if l)
		else:
			self.read_stations()
		self.stations_inv = dict([(l.lower(),k) for k,l in self.stations.iteritems()])

	def read_stations(self):
		namen = []
		for ci in xrange(0, 26):
			c = chr(ord('A')+ci)
			dumpname = "namen_%s.txt" % c
			if debugpiet and os.path.exists(dumpname):
				page = open(dumpname).read()
			else:
				page = pietlib.get_url('http://m.ns.nl/stations.action?key='+c, headers=[('Accept','text/html')])
				if debugpiet:
					open(dumpname,'w').write(page)
			namen = namen + re.findall('<p><a.*?>(.*?)</a> \((.*?)\)</p>', page)
		self.stations = {}
		out = open('stationnamen.txt', 'w')
		for lang,kort in namen:
			out.write('%s,%s\n' % (kort,lang))
			self.stations[kort.lower()] = lang

	def to_short(self, longname):
		longname = longname.lower()
		if longname in self.stations_inv:
			return self.stations_inv[longname]
		if longname in self.stations: # ok, het was eigenlijk al kort
			return longname

		# not found, assume longname is substring of a longname
		betterlongname = None
		for l,s in self.stations_inv.iteritems():
			if l.find(longname)>=0:
				if not betterlongname or len(betterlongname)>len(l):
					betterlongname = l

		if betterlongname:
			 return self.stations_inv.get(betterlongname)

		return None
			
	def to_long(self, shortname):
		shortname = shortname.lower()
		if shortname in self.stations:
			return self.stations[shortname]
		if shortname in self.stations_inv: # ok, het was eigenlijk al lang
			return shortname
		return None


stations = StationsNamen()

def ns_format_page(page):
	""" returns (have_found_reisadvies, pagetekst) """
	reflags = re.DOTALL | re.MULTILINE

	def replace_keywords(text):
		ns_translation = {
			'From': 'Van',
			'to': 'naar',
			'Departure': 'Vertrek',
			'D': 'V',
			'Centraal': 'CS',
			'Intercity': 'IC',
			'direction': 'r',
			'richting': 'r',
			'platform': 'spoor',
			'Railway construction work': 'onderhoud',
			'alleen 2e klas, Geen AVR-NS': '',
			'NS': '',
			'Fiets meenemen niet mogelijk': '',
			'Reserveren mogelijk': '',
			'Toeslag': '\003Toeslag\003',
		}
		regex = '|'.join('\\b%s\\b' % (k,) for k in ns_translation)
		def repl_word(w):
			w = w.group()
			return ns_translation[w]
		return re.sub(regex, repl_word, text)

	def format_va_block(text):
		text = text.group().split('\n')
		van = text[0].lstrip('V ') + ' ' + text[1]
		naar = text[-2].lstrip('A ') + ' ' + text[-1]
		rest = ', '.join(text[2:-2])
		return van + ' -> ' + naar + ', ' + rest

	def format_table(text):
		if text.find('class="travelPrice">')>0:
			return (False, '')

		is_reisadvies = text.find('class="travelPrice">')>0

		# lines are terminated by </td>, not by \n
		text = re.compile('[\n\r]', flags=reflags).sub('', text)
		text = text.replace('</td>', '\n')

		text = re.compile('<font color="red">(.*?)</font>', flags=reflags).sub('\003\\1\003 ', text)
		text = re.sub('<[^>]*>', '', text) # remove html tags
		text = text.replace('&#160;', ' ')
		text = text.replace('[+]', '')
		text = text.replace('\003\003', '')
		text = replace_keywords(text) # replace keywords defined above
		text = re.compile('[\n\r][\n\r ]*', flags=reflags).sub('\n', text) # remove empty lines

		text = re.sub(r'[ ]+spoor (\d+[abAB]?)', '(\\1)', text)
		text = re.compile(r'^V .*?^A .*?^.*?$', flags=reflags).sub(format_va_block, text)


		text = re.sub('[ \t]+', ' ', text) # remove redundant spaces
		return (is_reisadvies, text)

	# ---- actual start of function ----

	tables = re.findall('<table.*?</table>', page, flags=reflags)
	tables = [format_table(t) for t in tables]
	found_reisadvies = any(t[0] for t in tables)
	text = '\n'.join(t[1] for t in tables if t[1])
	return (found_reisadvies, text)


# -------------------------


def ns(regel, channel):
	def format_station(x_org, opmerkingen):
		x = {
			'rtc': 'rtd'
		}.get(x_org, x_org)
		if x != x_org:
			opmerkingen.append((x, x_org))
		if (x[0]=='"' and x[-1]=='"') or (x[0]=="'" and x[-1]=="'"):
			x = x[1:-1]
		y = stations.to_short(x)
		if not y:
			return x
		if x!=y:
			opmerkingen.append((y,stations.to_long(y)))
		return y

	pietlib.timezone_reset()

	if regel == "?":
		result = pietlib.get_url_soup("http://mobiel.ns.nl/mobiel/storingen.action")
		storingen = [ str(i.contents[0]) for i in result.body.findAll('h4') ]
		if storingen:
			return "er zijn storingen op:\n  " + "\n  ".join(storingen)
		else:
			return "er zijn geen storingen"

	if regel.lower().startswith("afk") or regel.lower().startswith("accr"):
		naam = regel.split(' ', 1)[1:]
		if not naam:
			return "ja, ik wil je best afkortingen geven, ook wel van stations"
		s = stations.to_short(naam[0])
		if not s:
			return "beter dan '%s' wordt het niet, daar is geen afkorting voor" % naam[0]
		return '%s (%s)' % (s, stations.to_long(s))

	qs = """\s*((?:["][^"]*["])|(?:['][^']*['])|(?:[^'"]\S*))\s*"""
	full = (
		"(?:van)?"+qs+
		"(?:naar)?"+qs+
		"(?:via"+qs+")?"+
		"(om|v\S*|a\S*)?\s*(\d+:\d{2})?\s*(hsl)?")

	r = re.match(full, regel)
	if not(r):
		return "uh, dus je wilt met de trein. verder snapte ik het allemaal niet"
	(van, naar, via, tijdtype, tijd, hsl) = r.groups()
	opmerkingen = []
	van = format_station(van, opmerkingen)
	naar = format_station(naar, opmerkingen)
	via = via and format_station(via, opmerkingen) or ""
	datum = time.strftime("%d-%m-%Y")
	tijdtype = not(tijdtype) or tijdtype=="om" or tijdtype[0]=="v"

	if opmerkingen:
		opm = [ "\002%s\002 voor %s" % (s,l) for s,l in opmerkingen ]
		piet.send(channel, "%s was korter geweest" % pietlib.make_list(opm))

	print "NS: van %s naar %s via %s %stijd %s" % (repr(van), repr(naar), repr(via), tijdtype and "vertrek" or "aankomst", repr(tijd))

	# test ns site en haal cookies
	cookies = []
	pietlib.get_url("http://mobiel.ns.nl/planner.action?lang=nl", outcookies=cookies, headers=[('Accept','text/html')])
	cookies = [ re.sub(';.*', '', c) for c in cookies ]

	postdata = {
		'from':van, 'to':naar, 'via':via,
		'date':datum, 'time':tijd, 'departure':(tijdtype and 'true' or 'false'),
		'planroute':'Reisadvies',
		'hsl':(hsl and 'true' or 'false')}

	for retrycount in range(1): # try max 5 times to get a correct page
		page = pietlib.get_url("http://mobiel.ns.nl/planner.action", postdata, incookies=cookies, headers=[('Accept','text/html')])
		open("nsresult.html", "w").write(page)
		reisadvies, page = ns_format_page(page)
		if reisadvies:
			break
	return page

if __name__ == '__main__':
	import sys
	piet.send = lambda x,y: sys.stdout.write("%s: %s\n" % (x,y))
	dotest = lambda cmd: sys.stdout.write("\nTest: %r\n%s\n" % (
				cmd, ns(cmd, 'channel').replace('\003', '!!!')))

	dotest('?')
	dotest('afko grou')
	dotest('afk ahpr')
	dotest('afk eindh')
	dotest('vb wezep')
	dotest('van grou naar ahpr aan 21:00')
	dotest('van enkhuizen naar zevenaar via vss 21:00')
	dotest('asd rtd 17:20 hsl')



