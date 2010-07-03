#!/usr/bin/python
# vim: set fileencoding=utf-8 :

import urllib, simplejson, pietlib

gps_cache = {}

def gps_lookup(params):
	global gps_cache
	params = params.strip()
	if params in gps_cache:
		return gps_cache[params]

	google_args = { 'address' : params, 'sensor' : 'false', 'language' : 'nl'}
	url = """http://maps.google.nl/maps/api/geocode/json?""" + urllib.urlencode(google_args)
	try:
		result = simplejson.loads(pietlib.get_url(url,maxsize=10*1024*1024))
	except Exception, e:
		print "google geocode request FAILED:"
		print " - url: %s" % url
		print " - exception: %r" % e
		raise Exception("could not fetch")
	
	status = result.get('status', 'geen status').lower()
	if status != "ok":
		print "google geocode returned %s, url: %s" % (status,url)
		raise Exception("not found")
	try:
		longnames = []
		for add in result['results'][0]['address_components']:
			name = add['long_name']
			if name.lower() != 'nederland' and name not in longnames:
				longnames.append(add['long_name'])
		lat = float(result['results'][0]['geometry']['location']['lat'])
		lng = float(result['results'][0]['geometry']['location']['lng'])
	except Exception, e:
		print "google geocode FAILED:"
		print " - url: %s" % url
		print " - exception: %r" % e
		raise Exception("could not parse")

	result = (longnames, (lat,lng))
	gps_cache[params] = result
	print "gps-lookup found %r" % (result,)
	return result


def graden(f):
	""" convert float to graden/minuten/seconden """
	mins = int(f)
	f = (f-mins) * 60
	secs = int(f)
	f = (f-secs) * 60
	return u"%d°%d'%.2f''" % (mins,secs,f)

def gps_coord(param):
	try:
		loc = gps_lookup(param)
	except:
		return "%r staat niet op de kaart" % param
	print repr(loc)

	lat,lng = loc[1]
	NS = lat >= 0 and "N" or "S"
	EW = lng >= 0 and "E" or "W"
	slat,slng = graden(abs(lat)),graden(abs(lng))
	
	return u"%s: %s: %s %s: %s (%.4f%s %.4f%s)" % (u', '.join(loc[0]), NS, slat, EW, slng, lat, NS, lng, EW)

if __name__ == '__main__':
	print gps_coord("haedstrjitte, reduzum")
	print gps_coord("voorburg")
	print gps_coord("schouwburg, sydney")
