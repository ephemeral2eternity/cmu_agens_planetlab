# Script to run dash experiments on PlanetLab nodes
import time
import random
import sys
import json
import operator
import urllib2, socket
from ping import *
from agent_util import *
from client_stat import *
from ant_dash import *
from rnd_dash import *

video = 'BBB'
port = 8615
client = getMyName()

## Query the centralized monitoring server to obtain a list of cache agents
srv_addrs = get_cache_agents()
srv_rtts = pingSrvs(srv_addrs)

## Get the closest cache agent
cache_agent = get_closest_agent(srv_rtts)

candidates = {
				"cache-07" : "130.211.63.102",
				"cache-08" : "130.211.95.77"
			}

clientID = client + "_RND_DASH"
print "Cache Agent", cache_agent
rnd_tr = rnd_dash(candidates, video, clientID)
rnd_stat = get_qoe_stat(rnd_tr)

clientID = client + "_ANT_DASH"
alpha = 0.5
print "Cache Agent", cache_agent
ant_tr = ant_dash(cache_agent, srv_addrs, candidates, port, video, clientID, alpha)
ant_stat = get_qoe_stat(ant_tr)

print "RND_DASH QoE Stats: ", rnd_stat
print "ANT_DASH QoE Stats: ", ant_stat
