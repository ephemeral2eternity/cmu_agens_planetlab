## Testing the cooperative client in CFD System
# test_coop_client.py
# Chen Wang, Feb. 18, 2015
# chenw@andrew.cmu.edu
import random
import sys
import os
import logging
import shutil
import time
from datetime import datetime
from simple_client import *
from test_utils import *
from client_utils import *


### Get client name and attache to the closest cache agent
client_name = getMyName()

### Cannot even obtain a cache agent
cache_agent_ip = '104.197.42.89'

## Denote the server info
srv_info = {}
srv_info['ip'] = '104.197.42.89'
srv_info['srv'] = 'cache-01'
video_name = 'BBB'

### Get the server to start streaming
for i in range(6):
	cur_ts = time.time()

	## Testing rtt based server selection
	waitRandom(1, 100)
	simple_client(cache_agent_ip, srv_info, video_name)

	time_elapsed = time.time() - cur_ts
	if time_elapsed < 600:
		time.sleep(600 - time_elapsed)
