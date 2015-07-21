import os
#import requests     PlanetLab nodes do not have package requests
import urllib2
import re
import xml.etree.ElementTree as ET

def num(s):
	try:
		return int(s)
	except ValueError:
		return float(s)

def mpd_parser(server_address, videoName):

	# server_address = 'ec2-54-76-42-64.eu-west-1.compute.amazonaws.com'
	# videoName = 'st'
	mpdFile = 'stream.mpd'

	url = 'http://' + server_address + '/' + videoName + '/' + mpdFile
	print "MPD URL: ", url
	#r = requests.get(url)

	try:
		r = urllib2.Request(url)
		f = urllib2.urlopen(r)
		mpdString = f.read()
		# mpdString = str(r.content)
		# print mpdString
	except:
		return {}

	representations = {}

	root = ET.fromstring(mpdString)
	mediaLengthStr = root.get('mediaPresentationDuration')[2:]
	mlA = re.findall(r'\d+', mediaLengthStr)
	if len(mlA) == 3:
		mediaLength = num(mlA[0])*3600 + num(mlA[1])*60 + num(mlA[2])
	elif len(mlA) == 2:
		mediaLength = num(mlA[0])*60 + num(mlA[1])
	elif len(mlA) == 1:
		mediaLength = num(mlA[0])
	else:
		print 'Parsing mpd file error, unrecognized mediaPresentationDuration!'
		sys.exit(1)

	minBufferTime = num(root.get('minBufferTime')[2:-1])
	for period in root:
		for adaptSet in period: 
			for rep in adaptSet:
				repType = rep.get('mimeType')
				repID = rep.get('id')
				repBW = rep.get('bandwidth')
				for seg in rep:
					initSeg = seg.get('initialization')
					segName = seg.get('media')
					segStart = seg.get('startNumber')
					segLength = seg.get('duration')
					timescale = seg.get('timescale')
				representations[repID] = dict(mtype=repType, name=segName, bw=repBW, initialization=initSeg, start=segStart, length=segLength, timescale=timescale)

	# for item in representations:
	#	print item
	f.close()

	return {'representations' : representations, 'mediaDuration':mediaLength, 'minBufferTime': minBufferTime}
