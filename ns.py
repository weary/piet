import re, urllib, time, pietlib, piet
import BeautifulSoup


class StationsNamen:
	# class that can translatie station-names to station-accroniems and back
	# works by retreiving from the net and caching.
	# note, a short name can have several long names, but we only store one, so
	# long_to_short(short_to_long(..)) might not return the input

	def __init__(self):
		self.short = {}
		self.long = {}
		
	def fetch(self, name): # either a long or a short name. returns the short name of the 'best match'
		name = name.lower().strip()
		s=pietlib.get_url('http://mobiel.ns.nl/mobiel/stations.action?station='+urllib.quote(name))
		namelist = re.findall("<strong>([^<]*)</strong>[^]]*\[([^]]*)", s)
		if not namelist:
			return None
		for (l,s) in namelist:
			l = l.lower().strip()
			s = s.lower().strip()
			self.short[s] = l
			self.long[l] = s
		return namelist[0][1].lower().strip()

	def to_short(self, long):
		long = long.lower()
		if long in self.long:
			return self.long[long]
		if long in self.short:
			return long # it wasn't long after all
		return self.fetch(long)

	def to_long(self, short):
		short = short.lower()
		if short in self.short:
			return self.short[short]
		if short in self.long:
			return short # it wasn't short after all
		short = self.fetch(short)
		if not short:
			return None
		return self.short[short]


stations = StationsNamen()

def ns(regel, channel):
	def format_station(x, opmerkingen):
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

	if regel.lower().startswith("afko") or regel.lower().startswith("accr"):
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
		"(om|v\S*|a\S*)?\s*(\d+:\d{2})?")

	r = re.match(full, regel)
	if not(r):
		return "uh, dus je wilt met de trein. verder snapte ik het allemaal niet"
	(van, naar, via, tijdtype, tijd) = r.groups()
	opmerkingen = []
	van = format_station(van, opmerkingen)
	naar = format_station(naar, opmerkingen)
	via = via and format_station(via, opmerkingen) or ""
	datum = time.strftime("%d-%m-%Y")
	tijdtype = not(tijdtype) or tijdtype=="om" or tijdtype[0]=="v"

	if opmerkingen:
		opm = [ "\002%s\002 voor %s" % (s,l) for s,l in opmerkingen ]
		piet.send(channel, "%s was korter geweest" % pietlib.make_list(opm))

	print "NS: van %s naar %s via %s %s %s", (repr(van), repr(naar), repr(via), repr(tijdtype), repr(tijd))

	def finderr(soup):
		# find the text in <div id="errors">
		c = soup.find("div", {"id":"errors"})
		if not(c): return None
		c = c.span
		if not(c): return None
		return str(c.contents[0])

	ircred = lambda x: re.sub('<font color="red">(.*?)</font>', '\00304\\1\003 ', str(x).replace('<font color="red"></font>', ''))
	notags = lambda x: re.sub('<[^>]*>', '', ircred(x)).replace('&nbsp;', ' ')

	postdata = {
		'from':van, 'to':naar, 'via':via,
		'date':datum, 'time':tijd, 'departure':(tijdtype and 'true' or 'false'),
		'planroute':'reisadvies'}
	
	for retrycount in range(5): # try max 5 times to get a correct page
		page = pietlib.get_url("http://mobiel.ns.nl/mobiel/planner.action", postdata)
		open("nsresult.html", "w").write(page)
		soup = BeautifulSoup.BeautifulSoup(page)
		err = finderr(soup)
		if err:
			return "najaah, ns-site wil je niet helpen, 't zei: "+err
		
		selectfields = soup.select
		if selectfields:
			field = str(selectfields['name'])
			val = str(selectfields.option['value'])
			piet.send(channel, "ik gebruik '%s' in plaats van '%s'" % (val, postdata[field]))
			postdata[field] = val
		else:
			break # got a correct page
	
	if not(soup.table):
		return "de ns site is weer's brak (of ik ben stuk..)"

	# ok, we hebben de goeie pagina, nu het resultaat eruit halen
	rows = soup.table.findAll("tr")
	out = []
	while rows:
		# delete additional information lines first (bikes allowed, etc)
		while len(rows)>3 and not rows[3].hr:
			del rows[2]
		tmp = rows[0].findAll('td')
		vertrektijd = notags(tmp[1].a.string).replace("V ", "")
		vertrekstation = notags(tmp[2].renderContents())
		tmp = rows[1].findAll('td')[1].contents
		beschrijving = str(tmp[0] + tmp[1].string) # 'Stoptrein NS richting Hengelo'
		tmp = rows[2].findAll('td')
		aankomsttijd = notags(tmp[1].b.string).replace("A ", "")
		aankomststation = notags(tmp[2].renderContents())
		del rows[:4]
		row = "%s %s, %s %s, %s" % (vertrektijd, vertrekstation, aankomsttijd,
				aankomststation, beschrijving)
		row = row.replace("&nbsp;", " ")
		row = re.sub(r" spoor ([0-9]+[ab]?)", lambda x: "(%s)" % x.group(1), row)
		row = row.replace("richting", "r").replace("Centraal", "cs").replace("Stoptrein", "boemel").replace("Intercity", "ic").replace("Sneltrein", "sneltrein").replace("NS ", "")
		row = re.sub(" *,", ",", row)
		out.append(row)
	if not(out):
		return "uh, het is me niet gelukt de route uit de pagina te parsen.."
	return '\n'.join(out)




