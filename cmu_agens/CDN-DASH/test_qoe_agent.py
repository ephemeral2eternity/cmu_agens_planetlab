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
from qoe_agent import *
from monitor.ping import *
from monitor.get_hop_info import *

## Denote the server info
# cdn_host = 'cmu-agens.azureedge.net'
# cdn_host = 'aws.cmu-agens.com'
cdn_host = 'az.cmu-agens.com'
video_name = 'BBB'

### Get the server to start streaming
locator = "40.76.72.2"
for i in range(1):
	## Testing rtt based server selection
	selected_srv_addr = cdn_host + '/videos/'
	# client_ID, CDN_SQS, uniq_srvs = qoe_agent(selected_srv_addr, video_name, locator)
	qoe_agent(selected_srv_addr, video_name, locator)

	# writeJson("TR_" + client_ID, all_srv_trace_data)