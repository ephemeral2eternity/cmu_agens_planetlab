## Testing the link adding in the cfds-logger
# Chen Wang, chenw@cmu.edu, July 23, 2015
# test_add_client_links.py
import random
import sys
from attach_cache_agent import *
from get_srv import *
from get_peer import *
from cfds_logger_utils import *

### Get client name and attache to the closest cache agent
client_name = getMyName()
cache_agent = attach_cache_agent()

## Get the initial streaming server
srv_info = get_srv(cache_agent['ip'], 1, "rtt")

## Get peer client from the streaming server or from the closest cache agent
pclient = get_peer(cache_agent['ip'], 'pclient')
vclient = get_peer(srv_info['ip'], 'vclient', pclient['name'])

## Log the edge of existing clients
update_edge_cfds_logger(client_name, pclient['name'], vclient['name'])