# Script to run dash experiments on PlanetLab nodes
import time
import random
import sys
import json
import os
import glob
import operator
import urllib2, socket
from ping import *
from qas_dash_agent import *
from cqas_dash_agent import *

## Get Client Agent Name
def getMyName():
	hostname = socket.gethostname()
	return hostname

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

## Get the closest cache agent to the client.
def get_closest_agent(srvRtts):
	sorted_srv_rtts = sorted(srvRtts.items(), key=operator.itemgetter(1))
	cache_agent = sorted_srv_rtts[0][0]
	return cache_agent

## Wait for a random interval of time
def waitRandom(minPeriod, maxPeriod):
	## Sleeping a random interval before starting the client agent
	waitingTime = random.randint(minPeriod, maxPeriod)
	print "Before running DASH on the client agent on %s, sleep %d seconds!" % (client, waitingTime)
	time.sleep(waitingTime)

## Check if a list or dict is empty
def is_empty(any_structure):
	if any_structure:
		return False
	else:
		return True

## Get Server Zones
def get_zones():
	plsrv = '146.148.66.148'
	url = "http://%s:8000/overlay/zone/"%plsrv
	req = urllib2.Request(url)
	srv_zones = {}
	try:
		res = urllib2.urlopen(req)
		res_headers = res.info()
		srv_zones = json.loads(res_headers['Params'])
	except urllib2.HTTPError, e:
		print "[Error-AGENP-Client] Failed to obtain avaialble cache agent list!"
	return srv_zones

## Get Server Regions
def get_regions(srv_zones):
	srv_regs = {}
	for key in srv_zones:
		srv_regs[key] = srv_zones[key].split('-')[0]
	return srv_regs

## Get the Closest Zone or Region
def get_closest(cache_agent_rtts, srv_zones):
	zone_rtts = {}
	zone_vms = {}
	for k,v in srv_zones.iteritems():
		zone_rtts[v] = 0
		zone_vms[v] = 0
	for k,v in srv_zones.iteritems():
		zone_rtts[v] = zone_rtts[v] + cache_agent_rtts[k]
		zone_vms[v] = zone_vms[v] + 1
	for key in zone_rtts:
		zone_rtts[key] = zone_rtts[key] / float(zone_vms[key])
	sorted_zone_rtts = sorted(zone_rtts.items(), key=operator.itemgetter(1))
	closest_zone = sorted_zone_rtts[0][0]
	# print sorted_zone_rtts
	return closest_zone

def get_srvs_in_zone(agent_zones, zone):
	zone_srvs = []
	for key in agent_zones:
		if zone in agent_zones[key]:
			zone_srvs.append(key)
	return zone_srvs

def read_latest_rtts():
        cache_agent_rtts = {}
        latestFile = max(glob.iglob('./log/*_PING.json'), key=os.path.getctime)
        all_srvs_rtts = json.load(open(latestFile))
        for key in all_srvs_rtts:
                if "gc" in key:
                        cache_agent = key.replace("gc", "cache-")
                        cache_agent_rtts[cache_agent] = all_srvs_rtts[key]
        return cache_agent_rtts

port = 8615
video = 'BBB'	
client = getMyName()

waitRandom(1, 100)

## Query the centralized monitoring server to obtain a list of cache agents
cache_agents = get_cache_agents()

## Get zones of cache agents
agent_zones = get_zones()

## Get regions of cache agents
agent_regions = get_regions(agent_zones)

if is_empty(cache_agents):
	print "[Error-AGENP-Client] The cache agent list is empty and the client agent program has exited!!!"
	sys.exit(0)

cache_agent_rtts = read_latest_rtts()
closest_zone = get_closest(cache_agent_rtts, agent_zones)

## Get servers in a server or region
srvs_closest_zone = get_srvs_in_zone(agent_zones, closest_zone)
print "Servers in the closest zone: ", srvs_closest_zone

cache_agent = get_closest_agent(cache_agent_rtts)

expID = 'exp2'
clientID = client + "_" + expID

## The first candidate server is the closest server
if cache_agent in srvs_closest_zone:
	srvs_closest_zone.remove(cache_agent)

candidates = {}
candidates[cache_agent] = cache_agents[cache_agent]

## The second candidate server is randomly selected from the closest zone
second_srv = random.choice(srvs_closest_zone)
candidates[second_srv] = cache_agents[second_srv]

## Save candidate servers for the experiment
candidatesFile = "./data/" + clientID + "_CANDS.json"
with open(candidatesFile, 'w') as outfile:
	json.dump(candidates, outfile, sort_keys = True, indent = 4, ensure_ascii = False)

## Run QAS_DASH client
qas_dash_agent(clientID, cache_agent, candidates, cache_agents, port, video)

## Wait 20 minutes between two types of clients
time.sleep(600)

## Run CQAS_DASH client
cqas_dash_agent(clientID, cache_agent, candidates, cache_agents, port, video)
