## Streaming Videos from a CDN and do traceroute and pings to the CDN
# trace_cdn.py
# Chen Wang, Mar. 3, 2016
# chenw@cmu.edu
import random
import sys
import os
import logging
import shutil
import time
from datetime import datetime
from dash_client import *
from monitor.ping import *
from monitor.get_hop_info import *

## Denote the server info
# cdn_host = 'cmu-agens.azureedge.net'
# cdn_host = 'aws.cmu-agens.com'
cdn_host = 'az.cmu-agens.com'
video_name = 'st'

### Get client name and attache to the closest cache agent
ext_ip, client_info = get_ext_ip()
srv_ip = host2ip(cdn_host)
client_info['server'] = srv_ip
srv_info = get_node_info(srv_ip)
## Traceroute all srvs
cdnHops = get_hop_by_host(cdn_host)
cdnHops.append(srv_info)
client_info['route'] = cdnHops
'''
for client_key in client_info.keys():
	if client_key == 'route':
		for node in client_info[client_key]:
			print node
	else:
		print client_key, client_info[client_key]
'''

### Get the server to start streaming
for i in range(1):
	## Testing rtt based server selection
	selected_srv_addr = cdn_host + '/videos/'
	client_ID, CDN_SQS, uniq_srvs = dash_client(selected_srv_addr, video_name)

	# writeJson("TR_" + client_ID, all_srv_trace_data)