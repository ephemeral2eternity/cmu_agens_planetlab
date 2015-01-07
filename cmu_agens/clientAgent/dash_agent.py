# Dash client agent on PlanetLab nodes
from client_agent import *
import operator
import json

# Define a function to run DASH client agent
def dash_agent(clientID, cache_agent, candidates, cache_agent_rtts, port, videoName):
	server_ips = candidates
	client = clientID.split("_")[0]

	# Get server addresses for candidate servers
	server_addrs = {}
	for srv in server_ips.keys():
		server_addrs[srv] = server_ips[srv] + ":" + str(port)

	# Get RTTs from candidate servers
	candidate_rtts = {}
	for srv in candidates:
		candidate_rtts[srv] = cache_agent_rtts[srv]

	## Upload the ping RTTs to google cloud storage
	#pingFile = "./data/" + clientID + "-PING.json"
	#with open(pingFile, 'w') as outfile:
	#	json.dump(candidate_rtts, outfile, sort_keys = True, indent = 4, ensure_ascii=False)

	# Use the closest server as selected server
	sorted_rtts = sorted(candidate_rtts.items(), key=operator.itemgetter(1))
	selected_srv = sorted_rtts[0][0]

	# Perform simple DASH streaming
	dashID = clientID + '_DASH'
	print "=========== DASH Streaming for " + dashID + "  ============="
	print "########## The cache agent is : " + cache_agent + "##############"
	print "########## The default selected server is : " + selected_srv + " ##############"
	dash(cache_agent, server_addrs, selected_srv, videoName, dashID)
