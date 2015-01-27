# Script to run dash experiments on PlanetLab nodes
import time
import random
import sys
import json
import operator
import urllib2, socket
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

port = 8615
video = 'BBB'	
client = getMyName()
waitRandom(1, 100)

## Query the centralized monitoring server to obtain a list of cache agents
cache_agents = get_cache_agents()

## Read PING file for the current client
cache_agent_rtts = json.load(open("./info/" + client + "_PING.json"))

## Read CLOSEST file for the current client
closest = json.load(open("./info/" + client + "_CLOSEST.json"))

print "=============== The closest server for Client: ", client, " is ", closest['Server'], " ======================"
print "=============== The closest zone for Client: ", client, " is ", closest['Region'], " ======================"
print "=============== The closest region for Client: ", client, " is ", closest['Zone'], " ======================"

selected_srv_ip = cache_agents[closest['Server']]

expID = 'exp1'
clientID = client + '_' + expID
simple_dash(video, clientID, selected_srv_ip)
