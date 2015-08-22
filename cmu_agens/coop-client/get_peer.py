## Get a peer client to cooperate
# Chen Wang, Jun. 17, 2015
# chenw@andrew.cmu.edu
## get_peer.py
import random
import socket
import urllib2
import json

## ======================================================================== 
# Get a random peer client from a list of peers
# @input: peer_list --- the list of peer nodes
# @return: peer_obj --- a random peer object that contains the peer name and the peer IP.
## ========================================================================
def get_rnd_peer(peer_list):
	peer_names = peer_list.keys()

	## Excluding the current host and excluding_name from the list
	hostname = socket.gethostname()

	if hostname in peer_names:
		peer_names.remove(hostname)

	rnd_peer_name = random.choice(peer_names)
	peer_info = {}
	peer_info['name'] = rnd_peer_name
	peer_info['ip'] = peer_list[rnd_peer_name]

	return peer_info

## ======================================================================== 
# Get a list (20) of peers closeby/streaming from the same server to cooperate
# @input: request_srv_ip ---- the server ip to send the request
#			cache agent ip: to get a client close by
#			video server ip: to get a client streaming from the same server
#		  peer_type ---- "pclient": get a peer client closeby
#						 "vclient" : get a peer client streaming from the same server
# @return: peer_list --- the dict that contains a list of peers.
#						 key : the client hostname
#						 value: the client ip 
## ========================================================================
def get_peers(request_srv_ip, peer_type):
	url = 'http://%s:8615/client/%s/' % (request_srv_ip, peer_type)
	print url

	## Get latest 20 peers from the request_srv_ip
	peers_info = {}
	try:
		rsp = urllib2.urlopen(url)
		rsp_headers = rsp.info()
		peer_list = json.loads(rsp_headers['Params'])
	except:
		print "get_peer failed"
		pass

	return peer_list



