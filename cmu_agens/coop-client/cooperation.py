## Fault Detection and Fault Tolerance via Client Cooperation
# Chen Wang, Jun. 17, 2015
# chenw@andrew.cmu.edu
## cooperation.py
import json
import urllib2
import sys
import socket
import time
from attach_cache_agent import *
from download_chunk import *
from get_srv import *
from get_peer import *
from mpd_parser import *
from cfds_logger_utils import *
from client_utils import *

## ======================================================================== 
# Get a peer's QoE info on the same video id it has requested
# @input: peer_ip ---- a peer client's ip
# @return: peer_latest_info --- the latest QoE info from the peer client
## ========================================================================
def get_peer_info_by_vid(peer_ip, vid_id):
	peer_url = "http://%s:8717/get?%d" % (peer_ip, vid_id)
	peer_vid_info = {}
	
	try:
		rsp = urllib2.urlopen(peer_url, timeout=1)
		rsp_headers = rsp.info()
		peer_vid_info = json.loads(rsp_headers['Params'])
		# print peer_vid_info
	except:
		print "Failed to connect to peer client", peer_ip
		pass

	return peer_vid_info

## ======================================================================== 
# Get a peer's latest QoE for cooperation
# @input: peer_ip ---- a peer client's ip
# @return: peer_latest_info --- the latest QoE info from the peer client
## ========================================================================
def get_peer_latest(peer_ip):
	peer_url = "http://%s:8717/latest" % peer_ip
	peer_latest_info = {}
	
	try:
		rsp = urllib2.urlopen(peer_url, timeout=1)
		rsp_headers = rsp.info()
		# rsp_html = rsp.read()
		peer_latest_info = json.loads(rsp_headers['Params'])
		# print peer_latest_info
		# print rsp_html
	except:
		print "Failed to connect to peer client", peer_ip
		pass

	return peer_latest_info

## ======================================================================== 
# Periodically select servers via BFT cooperation
# @input: mnQoE ---- the mean QoE for a cooperation period
#		  srv_info ---- the current server information
#		  video_id ---- the current video id the user is requesting
#         p_peers ---- the client peers that are close to the user.
# @return: new_srv_info --- a better server the client can switch to
## ========================================================================
def bft_srv_selection(mnQoE, srv_info, video_id, p_peers, v_peers):
	client_name = socket.gethostname()
	cur_p_peers = p_peers

	if mnQoE < 2:
		new_srv_info = {}
		## ===================================================================
		## BFT Algorithm to detect if it is a byzantine fault
		start_time = time.time()

		while (not new_srv_info) and cur_p_peers:
			new_srv_info = {}
			selected_p_peer = get_rnd_peer(cur_p_peers)
			pclient_vid = get_peer_info_by_vid(selected_p_peer['ip'], video_id)
			cur_p_peers.pop(selected_p_peer['name'])

			while (not pclient_vid) and cur_p_peers:
				pclient_vid = get_peer_info_by_vid(selected_p_peer['ip'], video_id)
				cur_p_peers.pop(selected_p_peer['name'])

			# peer_visit_ts = int(pclient_vid['ts'])
			if not pclient_vid:
				peer_qoe = -1
				break
			else:
				peer_qoe = float(pclient_vid['qoe'])

			if pclient_vid and (mnQoE < peer_qoe):
				new_srv_info['srv'] = pclient_vid["srvName"]
				new_srv_info['ip'] = pclient_vid["srv"]
				new_srv_info['vidName'] = srv_info['vidName']

		recovery_time = time.time() - start_time

		# client, fault_node, recovery_node, qoe, recovery_qoe, recovery_time, vidID, msg, fault_type
		recovery_msg_obj = {}
		if not new_srv_info:
			msg = "No better servers can be found from peer clients. Clients probably share a congested network!"
			msg_type = 3
			new_srv_info = srv_info
			recovery_msg_obj['recovery_peer'] = ""
		else:
			msg = "Switching server because of faults causing bad QoE in server side!"
			msg_type = 5
			recovery_msg_obj['recovery_peer'] = selected_p_peer['name']

		recovery_msg_obj['client'] = client_name
		recovery_msg_obj['faulty_node'] = srv_info['ip'] 
		recovery_msg_obj['recovery_node'] = new_srv_info['ip']

		recovery_msg_obj['qoe'] = mnQoE
		recovery_msg_obj['recovery_qoe'] = peer_qoe
		recovery_msg_obj['recovery_time'] = recovery_time
		recovery_msg_obj['video'] = video_id
		recovery_msg_obj['msg'] = "Recovery fault type " + str(msg_type) + " on server " + \
									srv_info['ip'] + " with time period : " + "{:10.4f}".format(recovery_time) + " seconds!"
		recovery_msg_obj['msg_type'] = msg_type

		local_recovery_msg_logger(recovery_msg_obj)
		recovery_msg_logger(recovery_msg_obj)

	else:
		new_srv_info = srv_info
		recovery_time = 0

	return new_srv_info



## ======================================================================== 
# Periodically select servers via client cooperation
# @input: mnQoE ---- the mean QoE for a cooperation period
#		  srv_info ---- the current server information
#		  video_id ---- the current video id the user is requesting
#         p_peers ---- the client peers that are close to the user.
# @return: new_srv_info --- a better server the client can switch to
## ========================================================================
def coop_qoe_srv_selection(mnQoE, srv_info, video_id, p_peers, v_peers):
	client_name = socket.gethostname()
	cur_p_peers = p_peers

	if mnQoE < 2:
		new_srv_info = {}
		## ===================================================================
		## Tolerate the fault causing bad QoE by finding another video server serving video_id
		start_time = time.time()

		while (not new_srv_info) and cur_p_peers:
			new_srv_info = {}
			selected_p_peer = get_rnd_peer(cur_p_peers)
			pclient_vid = get_peer_info_by_vid(selected_p_peer['ip'], video_id)
			cur_p_peers.pop(selected_p_peer['name'])

			while (not pclient_vid) and cur_p_peers:
				pclient_vid = get_peer_info_by_vid(selected_p_peer['ip'], video_id)
				cur_p_peers.pop(selected_p_peer['name'])

			# peer_visit_ts = int(pclient_vid['ts'])
			if not pclient_vid:
				peer_qoe = -1
				break
			else:
				peer_qoe = float(pclient_vid['qoe'])

			if pclient_vid and (mnQoE < peer_qoe):
				new_srv_info['srv'] = pclient_vid["srvName"]
				new_srv_info['ip'] = pclient_vid["srv"]
				new_srv_info['vidName'] = srv_info['vidName']

		recovery_time = time.time() - start_time

		# client, fault_node, recovery_node, qoe, recovery_qoe, recovery_time, vidID, msg, fault_type
		recovery_msg_obj = {}
		if not new_srv_info:
			msg = "No better servers can be found from peer clients. Clients probably share a congested network!"
			msg_type = 3
			new_srv_info = srv_info
			recovery_msg_obj['recovery_peer'] = ""
		else:
			msg = "Switching server because of faults causing bad QoE in server side!"
			msg_type = 5
			recovery_msg_obj['recovery_peer'] = selected_p_peer['name']

		recovery_msg_obj['client'] = client_name
		recovery_msg_obj['faulty_node'] = srv_info['ip'] 
		recovery_msg_obj['recovery_node'] = new_srv_info['ip']

		recovery_msg_obj['qoe'] = mnQoE
		recovery_msg_obj['recovery_qoe'] = peer_qoe
		recovery_msg_obj['recovery_time'] = recovery_time
		recovery_msg_obj['video'] = video_id
		recovery_msg_obj['msg'] = "Recovery fault type " + str(msg_type) + " on server " + \
									srv_info['ip'] + " with time period : " + "{:10.4f}".format(recovery_time) + " seconds!"
		recovery_msg_obj['msg_type'] = msg_type

		local_recovery_msg_logger(recovery_msg_obj)
		recovery_msg_logger(recovery_msg_obj)

	else:
		new_srv_info = srv_info
		recovery_time = 0

	return new_srv_info


## ======================================================================== 
# Tolerate Server Faults that causes a chunk request timeout in the VoD system
# @input: srv_info ---- the current server information
#		  video_id ---- the current video id the user is requesting
#		  vidChunk ---- the video chunk ID the current client is requesting
#		  v_peers ---- the client peers streaming from the same video
#         p_peers ---- the client peers that are close to the user.
# @return: server --- a better server the client can switch to
## ========================================================================
def coop_ft_srv_chunk(srv_info, video_id, vidChunk, v_peers, p_peers):
	## Excluding the video server issue
	vclient = get_rnd_peer(v_peers)
	vclient_latest = get_peer_latest(vclient['ip'])
	client_name = socket.gethostname()

	## ===================================================================
	# Check if the server is running to serve other clients
	# Resolve the fault type and log to both local logger and cfds-logger
	cur_v_peers = v_peers
	while (not vclient_latest) and cur_v_peers:
		print "Cannot connect to v_peer client: ", vclient['name'], ". Delete it from cur_v_peers list!"
		cur_v_peers.pop(vclient['name'])
		vclient = get_rnd_peer(v_peers)
		vclient_latest = get_peer_latest(vclient['ip'])

	if not vclient_latest:
		fault_msg_obj['client'] = client_name
		fault_msg_obj['node'] = srv_info['ip']
		fault_msg_obj['video'] = video_id
		fault_msg_obj['qoe'] = -1
		fault_msg_obj['msg'] = "The client " + client_name + " loses Internet connection!"
		fault_msg_obj['msg_type'] = msg_type

		local_fault_msg_logger(fault_msg_obj)
		fault_msg_logger(fault_msg_obj)

	vpeer_qoe = vclient_latest['qoe']
	vpeer_video = int(vclient_latest['video'])
	fault_msg_obj = {}
	if vpeer_qoe > 0:
		msg_type = 4
		msg = "The video server stops service or the video has been deleted by mistake."
	else:
		msg_type = 4
		msg = "The virtual machine the video server running on is crashed."
	
	fault_msg_obj['client'] = client_name
	fault_msg_obj['node'] = srv_info['ip']
	fault_msg_obj['video'] = video_id
	fault_msg_obj['qoe'] = -1
	fault_msg_obj['msg'] = msg
	fault_msg_obj['msg_type'] = msg_type

	local_fault_msg_logger(fault_msg_obj)
	fault_msg_logger(fault_msg_obj)

	## ===================================================================
	## Tolerate the fault by finding another video server serving video_id
	start_time = time.time()

	vchunk_sz = 0
	recovery_qoe = -1
	cur_p_peers = p_peers
	while (not vchunk_sz) and cur_p_peers:
		new_srv_info = {}
		selected_p_peer = get_rnd_peer(cur_p_peers)
		pclient_vid = get_peer_info_by_vid(selected_p_peer['ip'], video_id)

		while (not pclient_vid) and cur_p_peers:
			print "The client can not get video info for video id = ", str(video_id), " from p_peer: ", \
				selected_p_peer['name'], ", so this p_peer is removed from the list!"
			cur_p_peers.pop(selected_p_peer['name'])
			selected_p_peer = get_rnd_peer(cur_p_peers)
			pclient_vid = get_peer_info_by_vid(selected_p_peer['ip'], video_id)

		if pclient_vid:
			new_srv_info['srv'] = pclient_vid["srvName"]
			new_srv_info['ip'] = pclient_vid["srv"]
			new_srv_info['vidName'] = srv_info['vidName']
			vchunk_sz = download_chunk(new_srv_info['ip'], new_srv_info['vidName'], vidChunk)
			recovery_qoe = pclient_vid['qoe']

	recovery_time = time.time() - start_time
	if not vchunk_sz:
		fault_msg_obj = {}
		fault_msg_obj['client'] = client_name
		fault_msg_obj['node'] = srv_info['ip']
		fault_msg_obj['video'] = video_id
		fault_msg_obj['qoe'] = -1
		fault_msg_obj['msg'] = "Tried all closeby peer clients and cannot fix the fault in downloading \
		chunk " + vidChunk + " for video: " + srv_info['vidName'] + "\n" + "\n".join(p_peers.keys())
		fault_msg_obj['msg_type'] = 1
		local_fault_msg_logger(fault_msg_obj)
		fault_msg_logger(fault_msg_obj)
		sys.exit()

	# client, fault_node, recovery_node, qoe, recovery_qoe, recovery_time, vidID, msg, fault_type
	recovery_msg_obj = {}
	recovery_msg_obj['client'] = client_name
	recovery_msg_obj['faulty_node'] = srv_info['ip'] 
	recovery_msg_obj['recovery_node'] = new_srv_info['ip']
	recovery_msg_obj['recovery_peer'] = selected_p_peer['name']
	recovery_msg_obj['qoe'] = -1.0
	recovery_msg_obj['recovery_qoe'] = float(recovery_qoe)
	recovery_msg_obj['recovery_time'] = float(recovery_time)
	recovery_msg_obj['video'] = video_id
	recovery_msg_obj['msg'] = "Recovery fault type " + str(msg_type) + " on server " + \
								srv_info['ip'] + " with time period : " + "{:10.4f}".format(recovery_msg_obj['recovery_time']) + " seconds!"
	recovery_msg_obj['msg_type'] = msg_type

	local_recovery_msg_logger(recovery_msg_obj)
	recovery_msg_logger(recovery_msg_obj)

	return (new_srv_info, vchunk_sz)

## ======================================================================== 
# Tolerate mpd file faults in the video servers
# @input: srv_info ---- the current server information
#		  video_id ---- the current video id the user is requesting
#		  v_peers ---- the client peers streaming from the same video
#         p_peers ---- the client peers that are close to the user.
# @return: srv_obj --- a better server the client can switch to
## ========================================================================
def coop_ft_srv_mpd(cache_agent_ip, srv_info, video_id, v_peers, p_peers):
	## Excluding the video server issue
	vclient = get_rnd_peer(v_peers)
	vclient_latest = get_peer_latest(vclient['ip'])
	client_name = socket.gethostname()

	## ===================================================================
	# Check if the server is running to serve other clients
	# Resolve the fault type and log to both local logger and cfds-logger
	cur_v_peers = v_peers
	while (not vclient_latest) and cur_v_peers:
		cur_v_peers.pop(vclient['name'])
		vclient = get_rnd_peer(v_peers)
		vclient_latest = get_peer_latest(vclient['ip'])

	vpeer_qoe = float(vclient_latest['qoe'])
	fault_msg_obj = {}
	if vpeer_qoe > 0:
		msg_type = 6
		msg = "The redirector directs video request to a server that does not cache the video."
	else:
		msg_type = 4
		msg = "The video server is not running."
	
	fault_msg_obj['client'] = client_name
	fault_msg_obj['node'] = srv_info['ip']
	fault_msg_obj['video'] = video_id
	fault_msg_obj['qoe'] = -1
	fault_msg_obj['msg'] = msg
	fault_msg_obj['msg_type'] = msg_type

	local_fault_msg_logger(fault_msg_obj)
	fault_msg_logger(fault_msg_obj)

	## ===================================================================
	## Tolerate the fault by finding another video server serving video_id
	start_time = time.time()
	cur_p_peers = p_peers
	rsts = ''

	while (not rsts) and cur_p_peers:
		new_srv_info = {}
		selected_p_peer = get_rnd_peer(cur_p_peers)
		pclient_vid = get_peer_info_by_vid(selected_p_peer['ip'], video_id)

		while (not pclient_vid) and cur_p_peers:
			print "Cannot get video info for video id = ", str(video_id) + " from p_peer: " + \
					selected_p_peer['name'] + " Removing it from list!"
			cur_p_peers.pop(selected_p_peer['name'])
			selected_p_peer = get_rnd_peer(cur_p_peers)
			pclient_vid = get_peer_info_by_vid(selected_p_peer['ip'], video_id)

		if pclient_vid:
			print "New server name is: " + pclient_vid["srvName"]
			new_srv_info['srv'] = pclient_vid["srvName"]
			new_srv_info['ip'] = pclient_vid["srv"]
			new_srv_info['vidName'] = srv_info['vidName']
			rsts = mpd_parser(new_srv_info['ip'], new_srv_info['vidName'])

	recovery_time = time.time() - start_time
	if not rsts:
		fault_msg_obj = {}
		fault_msg_obj['client'] = client_name
		fault_msg_obj['node'] = srv_info['ip']
		fault_msg_obj['video'] = video_id
		fault_msg_obj['qoe'] = -1
		fault_msg_obj['msg'] = "Tried all closeby peer clients and cannot fix the fault in downloading \
		mpd file for video: " + srv_info['vidName'] + "\n" + "\n".join(p_peers.keys())
		fault_msg_obj['msg_type'] = 1
		local_fault_msg_logger(fault_msg_obj)
		fault_msg_logger(fault_msg_obj)
		sys.exit()

	# client, fault_node, recovery_node, qoe, recovery_qoe, recovery_time, vidID, msg, fault_type
	recovery_msg_obj = {}
	recovery_msg_obj['client'] = client_name
	recovery_msg_obj['faulty_node'] = srv_info['ip'] 
	recovery_msg_obj['recovery_node'] = new_srv_info['ip']
	recovery_msg_obj['recovery_peer'] = selected_p_peer['name']
	recovery_msg_obj['qoe'] = -1
	recovery_msg_obj['recovery_qoe'] = -1
	recovery_msg_obj['recovery_time'] = recovery_time
	recovery_msg_obj['video'] = video_id
	recovery_msg_obj['msg'] = "Recovery fault type " + str(msg_type) + " on server " + \
								srv_info['ip'] + " with time period : " + "{:10.4f}".format(recovery_time) + " seconds!"
	recovery_msg_obj['msg_type'] = msg_type

	local_recovery_msg_logger(recovery_msg_obj)
	recovery_msg_logger(recovery_msg_obj)

	return (new_srv_info, rsts)


## ======================================================================== 
# Tolerate Faults in the redirector
# Faults include: (1) redirector is not accessible
#				  (2) redirector does not return any video server for video_id
# @input: cache_agent_obj ---- The initial cache agent object.
#							including cache_agent_obj['ip']
#							including cache_agent_obj['name']
#		  video_id ---- The id of the requested video.
# @return: p_peers --- the closeby client peers
#		   cache_agent_obj --- the closest cache agent the user is connecting to.
## ========================================================================
def ft_cache_agent(cache_agent_obj, video_id):
	srv_info = get_srv(cache_agent_obj['ip'], video_id, "rtt")

	trial_num = 0
	while (not srv_info) and (trial_num < 3):
		print "The cache agent at ip=" + cache_agent_obj['ip'] + " is unaccessible. \
		Randomly get a new cache agent from the centralized controller cmu-agens!"
		# Attache to a new cache agent.
		cache_agent_obj = attach_cache_agent()
		srv_info = get_srv(cache_agent_obj['ip'], video_id, "rtt")
		trial_num = trial_num + 1

	if not srv_info:
		client_name = socket.gethostname()
		fault_msg_obj['client'] = client_name
		fault_msg_obj['node'] = cache_agent_obj['ip']
		fault_msg_obj['video'] = video_id
		fault_msg_obj['qoe'] = -1
		fault_msg_obj['msg'] = "The cache agent is not running and no running cache agents can be found in 4 tries!"
		fault_msg_obj['msg_type'] = 6
		local_fault_msg_logger(fault_msg_obj)
		fault_msg_logger(fault_msg_obj)
		sys.exit()

	return (srv_info, cache_agent_obj)

## ======================================================================== 
# Tolerate Faults in Cache Agent that no proximate peer clients are found
# Faults include: Cache Agent does not return any nearby peer clients
# @input: cache_agent_ip ---- the ip address of the closest cache agent
# @return: p_peers --- the closeby peer client list
## ========================================================================
def ft_pv_peers(cache_agent_ip, peer_type):
	peers = get_peers(cache_agent_ip, peer_type)

	trial_num = 0
	while (not peers) and (trial_num < 3):
		peers = get_peers(cache_agent_ip, peer_type)
		trial_num = trial_num + 1

	if not srv_info:
		client_name = socket.gethostname()
		fault_msg_obj['client'] = client_name
		fault_msg_obj['node'] = cache_agent_ip
		fault_msg_obj['video'] = -1
		fault_msg_obj['qoe'] = -1
		fault_msg_obj['msg'] = "The cache agent is not running and returns no recent p_peer/v_peer clients!"
		fault_msg_obj['msg_type'] = 7
		local_fault_msg_logger(fault_msg_obj)
		fault_msg_logger(fault_msg_obj)
		sys.exit()

	return peers



#==========================================================================================
# Main Function to test functions defined in this script
#==========================================================================================
def main(argv):
	'''
	### Test the get_peers and pop peer in p_peers list
	p_peers = get_peers("104.197.59.54", "pclient")
	cur_p_peers = p_peers
	selected_p_peer = get_rnd_peer(cur_p_peers)
	print selected_p_peer['name'], selected_p_peer['ip']
	pclient_latest = get_peer_latest(selected_p_peer['ip'])
	cur_p_peers.pop(selected_p_peer['name'])
	print cur_p_peers
	'''

if __name__ == '__main__':
    main(sys.argv)