#!/usr/bin/python
# -*- coding: iso-8859-1 -*-

import pietlib, shlex, simplejson, urllib, re, gps

class PietLookupFailure(Exception):
	pass

def maps_lookup(van, naar):
	def fail(reason):
		print "google maps request FAILED:"
		print " - url: %s" % url
		print " - %s" % reason
		raise PietLookupFailure("could not fetch")
	google_args = { 'origin' : van, 'destination' : naar,
	 	'sensor' : 'false', 'mode' : 'walking', 'language' : 'nl' }
	url = """http://maps.google.nl/maps/api/directions/json?""" + urllib.urlencode(google_args)
	try:
		result = simplejson.loads(pietlib.get_url(url,maxsize=10*1024*1024))
	except Exception, e:
		fail("fetch exception %r" % e)
	
	status = result.get('status', 'geen status').lower()
	if status == 'zero_results':
		return 'dat kan geen mens lopen, en kraaien vinden het vast ook maar niks'
	if status != "ok" or not result.get('routes'):
		print "google maps returned %s, url: %s" % (status,url)
		raise PietLookupFailure("not found")
	try:
		loopafstand = result['routes'][0]['legs'][0]['distance']['text']
		vancoords = result['routes'][0]['legs'][0]['start_location']
		naarcoords = result['routes'][0]['legs'][0]['end_location']
		vancoords = (vancoords['lat'], vancoords['lng'])
		naarcoords = (naarcoords['lat'], naarcoords['lng'])
	except Exception, e:
		fail("parse exception %r" % e)
	
	try:
		vanplaats = result['routes'][0]['legs'][0]['start_address']
	except:
		vanplaats = van
	try:
		naarplaats = result['routes'][0]['legs'][0]['end_address']
	except:
		naarplaats = naar

	vanplaats = vanplaats.replace(', Nederland', '')
	naarplaats = naarplaats.replace(', Nederland', '')
	return (vanplaats, vancoords, naarplaats, naarcoords, loopafstand)


def location(address):
	def fail(reason):
		print "google location request FAILED:"
		print " - url: %s" % url
		print " - %s" % reason
		raise PietLookupFailure("could not fetch location")

	google_args = { 'address':address, 'sensor':'false', 'region':'nl' }
	url = "http://maps.google.com/maps/api/geocode/json?" + urllib.urlencode(google_args)
	try:
		result = simplejson.loads(pietlib.get_url(url, maxsize=10*1024*1024))
	except Exception, e:
		fail("exception: %r" % e)
	if result["status"] != "OK":
		fail("status: %r" % result["status"])
	if "results" not in result:
		fail("no results in response")
	if len(result["results"]) < 1:
		fail("not enough results")
	if "geometry" not in result["results"][0]:
		fail("no geometry in result")
	location = result["results"][0]["geometry"]["location"]

	return location['lat'], location['lng']

def Distance(params):
	args = shlex.split(params.strip())
	if len(args) > 2:
		return "twee argumenten vind ik al moeilijk zat. doe eens rustig"
	if len(args) < 2:
		return "de afstand waartussen wil je hebben?"

	try:
		vanplaats, vancoords, naarplaats, naarcoords, loopafstand = maps_lookup(args[0], args[1])
	except:
		vanplaats, vancoords, naarplaats, naarcoords, loopafstand = None, None, None, None, None

	if not vanplaats:
		try:
			vanplaats, vancoords = gps.gps_lookup(args[0])
			vanplaats = vanplaats[0]
		except Exception, e:
			print "geo-lookup of %r failed, %s" % (args[0], e)
	if not naarplaats:
		try:
			naarplaats, naarcoords = gps.gps_lookup(args[1])
			naarplaats = naarplaats[0]
		except Exception, e:
			print "geo-lookup of %r failed, %s" % (args[1], e)

	if not vanplaats:
		return "na goed zoeken ben ik tot de conclusie gekomen dat %r niet bestaat" % args[0]
	if not naarplaats:
		return "na goed zoeken ben ik tot de conclusie gekomen dat %r niet bestaat" % args[1]

	def indo_graden(f):
		mins = int(f)
		f = (f-mins) * 60
		secs = int(f)
		f = (f-secs) * 60
		return '%d:%d:%d' % (mins,secs,int(round(f)))

	def indo_loc_to_string(lat,lng):
		NS = lat >= 0 and "N" or "S"
		EW = lng >= 0 and "E" or "W"
		lat,lng = indo_graden(abs(lat)),indo_graden(abs(lng))
		return "%s%s %s%s" % (lat, NS, lng, EW)

	url="http://www.indo.com/cgi-bin/dist?" + urllib.urlencode({
			'place1' : indo_loc_to_string(*vancoords), 'place2' : indo_loc_to_string(*naarcoords)})
	result = pietlib.get_url(url)

	result = re.findall('[0-9]+ miles [(]([0-9]+ km)[)]', result)
	if not result:
		return "even geen kraaien beschikbaar, maar als je gaat lopen van %s naar %s dan moet je %s ver" % (
				vanplaats, naarplaats, loopafstand)

	if not loopafstand:
		return "zoals een kraai vliegt van %s naar %s is het %s, en lopen is niet handig" % (
			vanplaats, naarplaats, result[0])
	
	return "zoals een kraai vliegt van %s naar %s is het %s, maar lopend is het %s" % (
			vanplaats, naarplaats, result[0], loopafstand)

if __name__ == '__main__':
	print Distance('"den haag" voorburg')
	print Distance('amsterdam enschede')
	print Distance('moskow milaan')

