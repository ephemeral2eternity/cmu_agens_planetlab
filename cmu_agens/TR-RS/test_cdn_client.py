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
from dash_client import *
from test_utils import *
from client_utils import *



### Get client name and attache to the closest cache agent
client_name = getMyName()

## Denote the server info
# srv_addr = 'www.cmu-agens.tk.global.prod.fastly.net/videos/'
# srv_addr = '23.251.129.31'
srv_addr = 'cache-01.cloudapp.net/videos/'
# srv_addr = 'az833905.vo.msecnd.net/videos/'
video_name = 'BBB'

### Get the server to start streaming
for i in range(1):
	cur_ts = time.time()

	## Testing rtt based server selection
	# waitRandom(1, 100)
	dash_client(srv_addr, video_name)

#time_elapsed = time.time() - cur_ts
#if time_elapsed < 600:
#	time.sleep(600 - time_elapsed)
