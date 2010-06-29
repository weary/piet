#!/usr/bin/python
# -*- coding: iso-8859-1 -*-

import pietlib, shlex, simplejson, urllib, re

def Distance(params):
	args = shlex.split(params.strip())
	if len(args) > 2:
		return "twee argumenten vind ik al moeilijk zat. doe eens rustig"
	if len(args) < 2:
		return "de afstand waartussen wil je hebben?"

	google_args = { 'origin' : args[0], 'destination' : args[1],
	 	'sensor' : 'false', 'mode' : 'walking', 'language' : 'nl' }
	url = """http://maps.google.nl/maps/api/directions/json?""" + urllib.urlencode(google_args)
	try:
		result = simplejson.loads(pietlib.get_url(url))
	except:
		return "google maps werkt niet mee (ik wil wel, echt!)"
	
	status = result.get('status', 'geen status').lower()
	if status == 'zero_results':
		return 'dat kan geen mens lopen, en kraaien vinden het vast ook maar niks'
	if status != "ok" or not result.get('routes'):
		print "google maps returned %s, url: %s" % (status,url)
		return "um, waar moet dat precies liggen?"
	try:
		loopafstand = result['routes'][0]['legs'][0]['distance']['text']
		van = result['routes'][0]['legs'][0]['start_location']
		naar = result['routes'][0]['legs'][0]['end_location']
		van = '%fN %fE' % (van['lat'], van['lng'])
		naar = '%fN %fE' % (naar['lat'], naar['lng'])
	except Exception, e:
		print "google maps FAILED:"
		print " - url: %s" % url
		print " - exception: %r" % e
		return "google maps api is blijkbaar veranderd. kan iemand me fixen?"
	
	try:
		vanplaats = result['routes'][0]['legs'][0]['start_address']
	except:
		vanplaats = args[0]
	try:
		naarplaats = result['routes'][0]['legs'][0]['end_address']
	except:
		vanplaats = args[1]

	vanplaats = vanplaats.replace(', Nederland', '')
	naarplaats = naarplaats.replace(', Nederland', '')


	url="http://www.indo.com/cgi-bin/dist?" + urllib.urlencode({'place1' : van, 'place2' : naar})
	result = pietlib.get_url(url)

	result = re.findall('[0-9]+ miles [(]([0-9]+ km)[)]', result)
	if not result:
		return "even geen kraaien beschikbaar, maar als je gaat lopen van %s naar %s dan moet je %s ver" % (vanplaats, naarplaats, loopafstand)
	
	return "zoals een kraai vliegt van %s naar %s is het %s, maar lopend is het %s" % (
			vanplaats, naarplaats, result[0], loopafstand)

if __name__ == '__main__':
	print Distance('delft "sydney, australie"')
