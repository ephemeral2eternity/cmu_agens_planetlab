# Script to run dash experiments on PlanetLab nodes
import time
import random
import sys
import json
import os
import glob
import operator
import urllib2, socket
import time
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

## Generate the candidate servers for QAS-DASH and CQAS-DASH
def get_candidates(closest_srv, cand_list, srv_ips, num):
	## The first candidate server is the closest server
	if closest_srv in cand_list:
		cand_list.remove(closest_srv)

	# Add the closest server as one of the candidates
	candidates = {}
	candidates[closest_srv] = srv_ips[closest_srv]

	## The second candidate server is randomly selected from the closest zone
	sampled_srvs = random.sample(cand_list, num - 1)
	for s in sampled_srvs:
		candidates[s] = srv_ips[s]
	return candidates

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
closest_region = get_closest(cache_agent_rtts, agent_regions)

## Get the closest server for the current client
srvs_closest_zone = get_srvs_in_zone(agent_zones, closest_zone)
srvs_closest_region = get_srvs_in_zone(agent_zones, closest_region)

## Get the closest cache agent
cache_agent = get_closest_agent(cache_agent_rtts)
closest_srv_ip = cache_agents[cache_agent]

exp_num = 200
for exp_id in range(1, exp_num + 1):
	ts = time.time()
	# expID = "exp" + str(exp_id)
	expID = str(int(ts))
	clientID = client + "_" + expID
	
	## Run baseline DASH client
	simple_dash(video, clientID, closest_srv_ip)

	## Get Intrazone Candidate Servers
	cand1 = get_candidates(cache_agent, srvs_closest_zone, cache_agents, 2)
	## Get Interzone Candidate Servers
	cand2 = get_candidates(cache_agent, srvs_closest_region, cache_agents, 2)

	## Save candidate servers for the experiment
	candidatesFile = "./data/" + clientID + "_intra_CANDS.json"
	with open(candidatesFile, 'w') as outfile:
		json.dump(cand1, outfile, sort_keys = True, indent = 4, ensure_ascii = False)
	candidatesFile = "./data/" + clientID + "_inter_CANDS.json"
	with open(candidatesFile, 'w') as outfile:
		json.dump(cand2, outfile, sort_keys = True, indent = 4, ensure_ascii = False)

	## Run Intra-zone server selection algorithms
	intra_clientID = clientID + "_intra"
	qas_dash_agent(intra_clientID, cache_agent, cand1, cache_agents, port, video)
	cqas_dash_agent(intra_clientID, cache_agent, cand1, cache_agents, port, video)
	
	## Run Inter-zone server selection algorithms
	inter_clientID = clientID + "_inter"
	qas_dash_agent(inter_clientID, cache_agent, cand2, cache_agents, port, video)
	cqas_dash_agent(inter_clientID, cache_agent, cand2, cache_agents, port, video)
