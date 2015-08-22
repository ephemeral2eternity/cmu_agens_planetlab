# Script to connect a client to the closest cache agent
import time
import random
import sys
import json
import logging
import sys
import operator
import urllib2, socket
from ping import *

# ================================================================================
## Get Client Agent Name
# ================================================================================
def getMyName():
	hostname = socket.gethostname()
	return hostname

# ================================================================================
# Query the list of all cache agents via the centralized monitor server cmu-agens.
# ================================================================================
def get_cache_agents():
	plsrv = '104.197.6.6'
	url = "http://%s:8000/overlay/node/"%plsrv
	req = urllib2.Request(url)
	cache_agents = {}
	try:
		res = urllib2.urlopen(req, timeout=1)
		res_headers = res.info()
		cache_agents = json.loads(res_headers['Params'])
	except:
		print "[Error-AGENP-Client] Failed to obtain availalble cache agent list!"
		pass
	return cache_agents

# ================================================================================
# Ping all servers saved in the dict candidates
# @input : candidates ---- server dict with key as server name and value as server ip
# ================================================================================
def pingSrvs(candidates):
	srvRtts = {}
	for srv in candidates.keys():
		srvRtts[srv] = getMnRTT(candidates[srv], 5)
		print "Ping ", srv, " : ", str(srvRtts[srv]), " ms"
	return srvRtts

# ================================================================================
# Check if cache agent is alive
# @input : cache_agent_ip ---- the ip address of cache agent to test
# @return : True --- alive
#			False --- dead
# ================================================================================
def is_alive(cache_agent_ip):
	url = 'http://%s:8615/video/getSrv?vidID=1&method=qoe'%cache_agent_ip
	print 'Testing if cache agent is alive:', url
	try:
		rsp = urllib2.urlopen(url)
		rsp_headers = rsp.info()
		srv_info = json.loads(rsp_headers['Params'])
		if srv_info:
			return True
		else:
			return False
	except:
		return False


## ======================================================================== 
# Connect the client to its closest cache agent
# @input : client ---- The client name
#		   cache_agent ---- The cache agent the client is connecting to
## ========================================================================
def connect_cache_agent(client, cache_agent, cache_agent_ip):
	update_url = "http://%s:8615/client/add?%s" % (cache_agent_ip, client)
	try:
		rsp = urllib2.urlopen(update_url)
		# print rsp
		print "Connect client :", client, " to its cache agent ", cache_agent, " successfully!"
	except:
		print "Failed to connect client ", client, " to its cache_agent", cache_agent, "!"

## ======================================================================== 
# Update the client's cache agent to cmu-agens
# @input : client ---- The client name
#		   cache_agent ---- The cache agent the client is connecting to
## ========================================================================
def update_cache_agent(client, cache_agent):
	update_url = "http://104.197.6.6:8000/cacheagent/add?client=%s&cache_agent=%s" % (client, cache_agent)
	try:
		rsp = urllib2.urlopen(update_url)
		print "Update cache agent for client :", client, " and its cache agent is ", cache_agent, " successfully!"
	except:
		print "Failed to update cache agent for client ", client, " to cmu-agens server!"

# ================================================================================
# Attach the closest cache agent to the client.
# @return : cache_agent_obj is the dict that saves the cache agent name and ip
#			cache_agent_obj['name'] --- the name of cache agent srv
#			cache_agent_obj['ip'] --- the ip of the attached cache agent
# ================================================================================
def attach_cache_agent():
	cache_agent_obj = {}

	## Try several times before exit
	all_cache_agents = get_cache_agents()
	trial_num = 0
	while not all_cache_agents and trial_num < 10:
		all_cache_agents = get_cache_agents()
		trial_num = trial_num + 1

	## Connect to the cache agent and tell the cache agent the client has connected
	client = getMyName()
	if all_cache_agents:
		srvRtts = pingSrvs(all_cache_agents)
		sorted_srv_rtts = sorted(srvRtts.items(), key=operator.itemgetter(1))
		for srv_rtt in sorted_srv_rtts:
			cache_agent = srv_rtt[0]
			cache_agent_obj['name'] = cache_agent
			cache_agent_obj['ip'] = all_cache_agents[cache_agent]
			if is_alive(cache_agent_obj['ip']):
				connect_cache_agent(client, cache_agent_obj['name'], cache_agent_obj['ip'])
				break
	else:
		logging.info("Agens client can not connect to any cache agent 20 times. The client might lose connection!!!")

	return cache_agent_obj
