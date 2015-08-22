## cfds_logger_utils.py
# All communications with cfds-logger for fault detection
# Chen Wang, chenw@andrew.cmu.edu, July, 23, 2015
import urllib2

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