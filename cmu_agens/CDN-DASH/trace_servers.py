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
servers = ["52.90.91.91", "162.209.106.193"]
video_name = 'BBB'

### Get the server to start streaming
all_srv_trace_data = {}
for srv in servers:
	## Testing rtt based server selection
	# selected_srv_addr = srv + '/videos/'
	# client_ID, SQS, uniq_srvs = dash_client(selected_srv_addr, video_name)

	## ping all servers
	mnRTT = getMnRTT(srv)
	print mnRTT

	## Traceroute all srvs
	cdnHops = get_hop_by_host(srv)
	print cdnHops

	traceData = {'RTT' : mnRTT, 'Hops' : cdnHops, 'TS' : time.time()}
	all_srv_trace_data[srv] = traceData.copy()

writeJson("USTR_" + client_name, all_srv_trace_data)