## Testing the CDN client in a VoD System
# test_cdn_client.py
# Chen Wang, Oct. 23, 2015
# chenw@cmu.edu
import random
import sys
import os
import logging
import shutil
import time
from datetime import datetime
from cdn_client import *
from test_utils import *
from client_utils import *
from monitor.ping import *
from monitor.traceroute import *
from monitor.load_vms import *

### Get client name and attache to the closest cache agent
client_name = getMyName()

## Denote the server info
srvs = load_vms()
video_name = 'BBB'

### Get the server to start streaming
for i in range(10):
	cur_ts = time.time()

	## ping all servers
	ping_file_name = 'ping@' + client_name + '@' + str(int(cur_ts))
	srvPINGs = pingVMs(srvs)
	selectedSrv = srvs[min(srvPINGs, key=lambda k: srvPINGs[k])]['ip']
	selected_srv_addr = selectedSrv + '/videos/'
	writeJson(ping_file_name, srvPINGs)

	cur_ts = time.time()

	## Traceroute all srvs
	tr_file_name = 'tr@' + client_name + '@' + str(int(cur_ts))
	srvHops = trVMs(srvs)
	writeJson(tr_file_name, srvHops)

	## Testing rtt based server selection
	# waitRandom(1, 100)
	cdn_client(selected_srv_addr, video_name)

#time_elapsed = time.time() - cur_ts
#if time_elapsed < 600:
#	time.sleep(600 - time_elapsed)
