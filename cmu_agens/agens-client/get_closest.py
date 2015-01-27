# Script to run dash experiments on PlanetLab nodes
import time
import random
import sys
import json
import operator
import urllib2, socket
from ping import *
from dash_agent import *

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

## Ping Candidate Servers
def pingSrvs(candidates):
	srvRtts = {}
	for srv in candidates.keys():
		srvRtts[srv] = getMnRTT(candidates[srv], 5)
	return srvRtts

## Attach the closest cache agent to the client.
def attach_cache_agent(srvRtts):
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
	print sorted_zone_rtts
	return closest_zone

port = 8615
video = 'BBB'	
client = getMyName()

#waitRandom(1, 100)

## Query the centralized monitoring server to obtain a list of cache agents
cache_agents = get_cache_agents()

## Get zones of cache agents
agent_zones = get_zones()
print agent_zones

## Get regions of cache agents
agent_regions = get_regions(agent_zones)
print agent_regions

if is_empty(cache_agents):
	print "[Error-AGENP-Client] The cache agent list is empty and the client agent program has exited!!!"
	sys.exit(0)

## Ping all cache agents and attache current client agent to the closest cache agent
cache_agent_rtts = pingSrvs(cache_agents)

## Get the closest zone for the current client
closest_zone = get_closest(cache_agent_rtts, agent_zones)

## Get the closest region for the current client
closest_region = get_closest(cache_agent_rtts, agent_regions)

# Upload the ping RTTs to google cloud storage
pingFile = "./info/" + client + "_PING.json"
with open(pingFile, 'w') as outfile:
	json.dump(cache_agent_rtts, outfile, sort_keys = True, indent = 4, ensure_ascii=False)

cache_agent = attach_cache_agent(cache_agent_rtts)
print "=============== The closest server for Client: ", client, " is ", cache_agent, " ======================"
print "=============== The closest zone for Client: ", client, " is ", closest_zone, " ======================"
print "=============== The closest region for Client: ", client, " is ", closest_region, " ======================"

client_closest = {}
client_closest['Server'] = cache_agent
client_closest['Zone'] = closest_zone
client_closest['Region'] = closest_region

# Upload the ping RTTs to google cloud storage
pingFile = "./info/" + client + "_CLOSEST.json"
with open(pingFile, 'w') as outfile:
	json.dump(client_closest, outfile, sort_keys = True, indent = 4, ensure_ascii=False)
