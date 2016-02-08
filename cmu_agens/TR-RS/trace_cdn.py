## Streaming Videos from a CDN and do traceroute and pings to the CDN
# trace_cdn.py
# Chen Wang, Jan. 3, 2016
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

### Get client name and attache to the closest cache agent
client_name = getMyName()

## Denote the server info
# cdn_host = 'cmu-agens.azureedge.net'
# cdn_host = 'aws.cmu-agens.com'
cdn_host = 'rs-cdn.cmu-agens.com'
video_name = 'BBB'

### Get the server to start streaming
for i in range(10):

	## Testing rtt based server selection
	selected_srv_addr = cdn_host + '/videos/'
	client_ID, CDN_SQS, uniq_srvs = dash_client(selected_srv_addr, video_name)

	all_srv_trace_data = {}
	for srv in uniq_srvs:
		## ping all servers
		mnRTT = getMnRTT(srv)
		print mnRTT

		## Traceroute all srvs
		cdnHops = get_hop_by_host(srv)
		print cdnHops

		traceData = {'RTT' : mnRTT, 'Hops' : cdnHops, 'TS' : time.time()}
		all_srv_trace_data[srv] = traceData.copy()

	writeJson("TR_" + client_ID, all_srv_trace_data)