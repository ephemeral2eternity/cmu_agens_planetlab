## cfds_logger_utils.py
# All communications with cfds-logger for fault detection
# Chen Wang, chenw@andrew.cmu.edu, July, 23, 2015
import urllib2
import urllib
import socket
import logging

## ======================================================================== 
# Update the client's hostname and ip address to the centralized cfds-logger
# @input : client ---- The client name
## ========================================================================
def update_client_cfds_logger(client):
	update_url = "http://173.255.112.124:8000/monitor/add?%s" % client
	try:
		rsp = urllib2.urlopen(update_url)
		print "Successfully update the client name: ", client, " to the centralized cfds-logger!"
	except:
		print "Failed to update client ", client, " to the centralized cfds-logger server!"

## ======================================================================== 
# Update the client's peers and their edges to the centralized cdfs-logger
# @input : src ---- The current client hostname
#		   pdst ---- The closeby peer client hostname
#		   vdst ---- The hostname of the peer client that streams video from
#					 the same video server as the src client.
## ========================================================================
def update_edge_cfds_logger(src, pdst, vdst):
	update_url = "http://173.255.112.124:8000/monitor/edge?src=%s&pdst=%s&vdst=%s" % (src, pdst,vdst)
	try:
		rsp = urllib2.urlopen(update_url)
		data = rsp.read()
		print data
	except:
		print "Failed to update links from src=", src, " to pdst=", pdst, " and vdst=", vdst

## ======================================================================== 
# Log error to the centralized cfds-logger
# @input : fault_msg_obj ---- the fault mesage object including following keys.
#		   client ---- The current client hostname
#		   node ---- The hostname of the impacted node
#		   vidID ---- The impacted video ID
#		   msg ---- The content of the error message
#		   msg_type ----- The identifier of the type of the message
## ========================================================================
def fault_msg_logger(fault_msg_obj):
	logger_url = "http://173.255.112.124:8000/logger/add"

	# Post the request to the centralized logger
	fault_data = urllib.urlencode(fault_msg_obj)
	msg_logger_url = logger_url + '?' + fault_data
	print msg_logger_url

	# Send to the cfds-logger
	try:
		rsp = urllib2.urlopen(msg_logger_url)
		rsp_data = rsp.read()
		print rsp_data
	except:
		print "Failed to log fault events to the cfds-logger!"

## ======================================================================== 
# Log recovery message to the centralized cfds-logger
# @input : recovery_msg_obj ---- the recovery mesage object including following keys.
#		   'client' ---- The current client hostname
#		   'faulty_node' ---- The node that is faulty and needs to be replaced
#		   'recovery_node' ---- The node that is obtained from other clients via client cooperation
#		   'qoe' ---- The QoE the client experiences with the faulty node
#          'recovery_qoe' ----- The QoE the client is supposed to experience with the recovery node
#		   'vidID' ---- The impacted video ID
#		   'recovery_time' ---- The time period the client takes to recover the fault
#		   'msg' ---- The content of the error message
#		   'fault_type' ----- The identifier of the type of the message
## ========================================================================
def recovery_msg_logger(recovery_msg_obj):
	logger_url = "http://173.255.112.124:8000/logger/rmsg"

	# Post the request to the centralized logger
	recovery_data = urllib.urlencode(recovery_msg_obj)
	msg_logger_url = logger_url + '?' + recovery_data

	print msg_logger_url
	# Send to the cfds-logger
	try:
		rsp = urllib2.urlopen(msg_logger_url)
		rsp_data = rsp.read()
		print rsp_data
	except:
		print "Failed to log fault events to the cfds-logger!"

## ======================================================================== 
## Testing the above functions
## ======================================================================== 
if __name__ == "__main__":
	'''
	## Test the sys_traceroute function
    hops = sys_traceroute('104.197.6.6')
    print hops
    ## Test the fault_msg_logger(fault_msg_obj)
	client_name = socket.gethostname()
	fault_msg_obj = {}
	fault_msg_obj['client'] = client_name
	fault_msg_obj['node'] = '104.197.59.54'
	fault_msg_obj['video'] = -1
	fault_msg_obj['qoe'] = -1
	fault_msg_obj['msg'] = "The cache agent is not running and returns no recent p_peer/v_peer clients!"
	fault_msg_obj['msg_type'] = 7
	fault_msg_logger(fault_msg_obj)
	'''

    ## Test the fault_msg_logger(fault_msg_obj)
	recovery_msg_obj = {}
	msg_type = 5
	client_name = socket.gethostname()
	recovery_msg_obj['client'] = client_name
	recovery_msg_obj['faulty_node'] = '104.197.59.54'
	recovery_msg_obj['recovery_node'] = '104.197.42.89'
	recovery_msg_obj['recovery_peer'] = '198.133.224.147'
	recovery_msg_obj['qoe'] = 1
	recovery_msg_obj['recovery_qoe'] = 4
	recovery_msg_obj['recovery_time'] = 0.02
	recovery_msg_obj['video'] = 2
	recovery_msg_obj['msg'] = "Recovery fault type " + str(msg_type) + " on server " + \
								'104.197.42.89' + " with time period : " + "{:10.4f}".format(recovery_msg_obj['recovery_time']) + " seconds!"
	recovery_msg_obj['msg_type'] = msg_type
	recovery_msg_logger(recovery_msg_obj)
