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

port = 8615
video = 'BBB'	
client = getMyName()

waitRandom(1, 100)

## Query the centralized monitoring server to obtain a list of cache agents
cache_agents = get_cache_agents()

if is_empty(cache_agents):
	print "[Error-AGENP-Client] The cache agent list is empty and the client agent program has exited!!!"
	sys.exit(0)

## Ping all cache agents and attache current client agent to the closest cache agent
cache_agent_rtts = pingSrvs(cache_agents)

# Upload the ping RTTs to google cloud storage
pingFile = "./data/" + client + "_DASH_PING.json"
with open(pingFile, 'w') as outfile:
	json.dump(cache_agent_rtts, outfile, sort_keys = True, indent = 4, ensure_ascii=False)

cache_agent = attach_cache_agent(cache_agent_rtts)
print "=============== Cache Agent for Client: ", client, " is ", cache_agent, " ======================"

expNum = 1

for i in range(1, expNum + 1):
	expID = 'exp' + str(i)
	candidate_srvs = random.sample(set(cache_agents.keys()), 2)
	candidates = {}
	for s in candidate_srvs:
		candidates[s] = cache_agents[s]
	clientID = client + "_" + expID

	## Save candidate servers for the experiment
	candidatesFile = "./data/" + clientID + "_DASH_CANDS.json"
	with open(candidatesFile, 'w') as cFile:
		json.dump(candidates, cFile, sort_keys = True, indent = 4, ensure_ascii = False)

	print "Selected candidate servers for ", clientID, " are :"
	for srv in candidate_srvs:
		print srv
	dash_agent(clientID, cache_agent, candidates, cache_agent_rtts, port, video)
	waitRandom(10, 1000)
