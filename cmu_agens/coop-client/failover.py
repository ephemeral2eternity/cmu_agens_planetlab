## Failover Control in the client side
# Chen Wang, Feb. 18, 2015
# chenw@andrew.cmu.edu
# failover.py
import logging
from get_srv import *

## ============================================================================================================================
# Get a new server to download the content when there is request timeout with one server.
# @input: client_ID ---- the client that has suffered request timeout with a server
#		  video_id ---- the video ID the client is requesting
#		  method ---- the method that the client is using
#		  cache_agent_ip ---- the closest server the client is connecting to
# @return: srv_info ---- the new server information
## ============================================================================================================================
def srv_failover(client_ID, video_id, method, cache_agent_ip):
	logging.info("[" + client_ID + "]Agens client can not get srv_info for video " + str(video_id) + " with method " + method + \
		" on cache agent " + cache_agent_ip + ". Try again to get the srv_info!!!")
	srv_info = get_srv(cache_agent_ip, video_id, method)
	if not srv_info:
		logging.info("[" + client_ID + "]Agens client can not get srv_info for video " + str(video_id) + " with method " + method + \
			" on cache agent " + cache_agent_ip + " twice. Stops requesting for methods rather than qoe!!!")
		print "[" + client_ID + "] Agens client can not get srv_info for video " + str(video_id) + " with method " + method + \
			" on cache agent " + cache_agent_ip + " twice. Stops requesting for methods rather than qoe!"
		if method == "qoe":
			trial_time = 0
			## Re-send the request to the cache agent up to 10 times until the server info is got
			while not srv_info and trial_time < 10:
				logging.info("[" + client_ID + "]Agent is a QoE-based control agent, keep getting a server for the video until 10 trials!!!")
				print "[" + client_ID + "]Agent is a QoE-based control agent, keep getting a server for the video." + "Trial: " + str(trial_time)
				srv_info = get_srv(cache_agent_ip, video_id, method)
				trial_time = trial_time + 1

	return srv_info