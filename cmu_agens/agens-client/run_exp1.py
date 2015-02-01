# Script to run dash experiments on PlanetLab nodes
import time
import random
import sys
import json
import operator
import urllib2, socket
import glob
import os
from ping import *
from client_agent import *

## Get Client Agent Name
def getMyName():
	hostname = socket.gethostname()
	return hostname

## Wait for a random interval of time
def waitRandom(minPeriod, maxPeriod):
	## Sleeping a random interval before starting the client agent
	waitingTime = random.randint(minPeriod, maxPeriod)
	print "Before running DASH on the client agent on %s, sleep %d seconds!" % (client, waitingTime)
	time.sleep(waitingTime)

## Query the list of all cache agents via our PlanetLab node monitor server.
def get_cache_agents():
        plsrv = '146.148.66.148'
        url = "http://%s:8000/overlay/node/"%plsrv
        req = urllib2.Request(url)
        cache_agents = {}
        try:
                res = urllib2.urlopen(req)
                res_headers = res.info()
                cache_agents = json.loads(res_headers['Params'])
        except urllib2.HTTPError, e:
                print "[Error-AGENP-Client] Failed to obtain avaialble cache agent list!"
        return cache_agents

def read_latest_rtts():
	cache_agent_rtts = {}
	latestFile = max(glob.iglob('./log/*_PING.json'), key=os.path.getctime)
	all_srvs_rtts = json.load(open(latestFile))
	for key in all_srvs_rtts:
		if "gc" in key:
			cache_agent = key.replace("gc", "cache-")
			cache_agent_rtts[cache_agent] = all_srvs_rtts[key]
	return cache_agent_rtts

## Get the closest cache agent to the client.
def get_closest_cache(srvRtts):
        sorted_srv_rtts = sorted(srvRtts.items(), key=operator.itemgetter(1))
        cache_agent = sorted_srv_rtts[0][0]
        return cache_agent


port = 8615
video = 'BBB'	
client = getMyName()
waitRandom(1, 100)

## Query the centralized monitoring server to obtain a list of cache agents
cache_agents = get_cache_agents()

## Read PING file for the current client
cache_agent_rtts = read_latest_rtts()

## Get the closest server for the current client
selected_srv_ip = get_closest_cache(cache_agent_rtts)

expID = 'exp1'
clientID = client + '_' + expID
simple_dash(video, clientID, selected_srv_ip)
