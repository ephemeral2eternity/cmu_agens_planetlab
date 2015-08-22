## Get a peer client to cooperate
# Chen Wang, Jun. 17, 2015
# chenw@andrew.cmu.edu
## get_peer.py
import random
import socket
import urllib2
import json

## ======================================================================== 
# Get a peer client closeby/streaming from the same server to cooperate
# @input: request_srv_ip ---- the server ip to send the request
#			cache agent ip: to get a client close by
#			video server ip: to get a client streaming from the same server
#		  peer_type ---- "pclient": get a peer client closeby
#						 "vclient" : get a peer client streaming from the same server
# @return: peer_obj --- the object that contains the peer name and the peer IP.
## ========================================================================
def get_peer(request_srv_ip, peer_type, excluding_name=None):
	url = 'http://%s:8615/client/%s/' % (request_srv_ip, peer_type)
	# print url

	## Get latest 20 peers from the request_srv_ip
	peers_info = {}
	try:
		rsp = urllib2.urlopen(url)
		rsp_headers = rsp.info()
		peers_info = json.loads(rsp_headers['Params'])
	except:
		print "get_peer failed"
		pass

	## Randomly get one peer and return
	peer_info = {}
	peer_list = peers_info.keys()
	# print peer_list

	## Excluding the current host and excluding_name from the list
	hostname = socket.gethostname()

	if hostname in peer_list:
		peer_list.remove(hostname)

	## Excluding the denoted client_host from the list
	if excluding_name:
		if excluding_name in peer_list:
			peer_list.remove(excluding_name)

	rnd_peer_name = random.choice(peer_list)
	peer_info['name'] = rnd_peer_name
	peer_info['ip'] = peers_info[rnd_peer_name]

	return peer_info


