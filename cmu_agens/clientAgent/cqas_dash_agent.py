# Test client agent file, client_agent.py
from client_agent import *
from ping import *
import operator

# Define a function to run DASH, QAS_DASH and CQAS_DASH in one client
def cqas_dash_agent(clientID, cache_agent, candidates, cache_agents, port, videoName):
	server_ips = cache_agents
	client = clientID.split("_")[0]

	## Get server addresses for candidate servers
	# server_addrs = {}
	#for srv in server_ips.keys():
	#	server_addrs[srv] = server_ips[srv] + ":" + str(port)

	# Perform QAS DASH streaming
	cqasdashID = clientID + '_CQAS'
	print "=========== CQAS-DASH Streaming for " + cqasdashID + "  ============="
	print "########## The cache agent is : " + cache_agent + ". ##############"
	alpha = 0.5
	cqas_dash(cache_agent, server_ips, candidates, port, videoName, cqasdashID, alpha)
