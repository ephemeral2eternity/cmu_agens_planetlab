# trace_cdn.py
# Chen Wang, Mar. 3, 2016
## chenw@cmu.edu
#### Report the route of the CDN video session to manager : http://manage.cmu-agens.com/verify
#### Pick up 10 nodes to do traceroute and get the verify agents
from monitor.get_hop_info import *
from communication.comm_manager import *
from communication.connect_cloud_agent import *
import random
from utils.test_utils import *

## Denote the server info
# cdn_host = 'cmu-agens.azureedge.net'
# cdn_host = 'aws.cmu-agens.com'
cdn_host = 'az.cmu-agens.com'
video_name = 'BBB'
# manager = 'superman.andrew.cmu.edu:8000'
manager = 'manage.cmu-agens.com'

## Connect cloud agent and add the client itself to available clients in the manager
cloud_agent = connect_cloud_agent(manager)

## Traceroute to the CDN to get the video session
ext_ip, client_info = get_ext_ip()
srv_ip = host2ip(cdn_host)
srv_info = get_node_info(srv_ip, "server")
## Traceroute all srvs
cdnHops = get_hop_by_host(cdn_host)
client_info['server'] = srv_info
client_info['route'] = cdnHops

waitRandom(1, 100)
success = report_video_session(manager, client_info)
if success:
    print "Successfully report nodes on sesssion of (%s, %s) to manager!" % (client_info['ip'], client_info['server']['ip'])
else:
    print "Failed to run http://manage.cmu-agens.com/verify/add_video_session!"

#### Obtain verification agents
K = 10
all_nodes = get_all_nodes(manager)
if 'client' in all_nodes.keys():
    available_agents = [agent['ip'] for agent in all_nodes['client']]
    available_agents.remove(client_info['ip'])
    random.shuffle(available_agents)
    chosen_agents = available_agents[:K]
    print chosen_agents

    for agent_ip in chosen_agents:
        agent_cdn_hops = get_hop_by_host(agent_ip)
        srv_info = get_node_info(agent_ip, "server")
        client_info['server'] = srv_info
        client_info['route'] = agent_cdn_hops

        waitRandom(1, 100)

        success = report_verify_session(manager, client_info)
        if success:
            print "Successfully report nodes on session (%s, %s) to manager!" % (client_info['ip'], client_info['server']['ip'])
        else:
            print "Failed to run http://manage.cmu-agens.com/verify/add_verify_session!"

else:
    print "Failed to obtain the list of clients"

### Get the server to start streaming
#for i in range(1):
#	## Testing rtt based server selection
#	selected_srv_addr = cdn_host + '/videos/'
#	client_ID, CDN_SQS, uniq_srvs = dash_client(selected_srv_addr, video_name)

	# writeJson("TR_" + client_ID, all_srv_trace_data)