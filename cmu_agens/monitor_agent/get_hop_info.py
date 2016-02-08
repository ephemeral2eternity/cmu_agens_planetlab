## Do Traceroute to a CDN host and gets detailed info on each hop.
# test_cdn_client.py
# Chen Wang, Oct. 23, 2015
# chenw@cmu.edu
import json
import os
from utils import *
from monitor.traceroute import *
from ipinfo.host2ip import *
from ipinfo.ipinfo import *

def get_hop_by_user(hop_file):
    ### Get client name and attache to the closest cache agent
    client_name = getMyName()
    # client_name = '75-130-96-12.static.oxfr.ma.charter.com'
    hop_data_folder = os.getcwd() + '/hopData/'
    hops_on_user = json.load(open(hop_file))
    if client_name in hops_on_user.keys():
        hops = hops_on_user[client_name]
        for hop in hops.keys():
            hop_info = ipinfo(hop)
            save_ipinfo(hop_data_folder, hop_info)
            print hop_info

def get_hop_by_host(cdn_host):
    hop_data_folder = os.getcwd() + '/hopData/'

    hops = traceroute(cdn_host)
    print hops

    hop_ids = sorted(hops.keys(), key=int)
    for hop_id in hop_ids:
        cur_hop_ip = hops[hop_id]['IP']
        if cur_hop_ip is '*':
            continue

        if not is_reserved(cur_hop_ip):
            hop_info = ipinfo(cur_hop_ip)
            save_ipinfo(hop_data_folder, hop_info)
            print hop_info

if __name__ == "__main__":
    ## Denote the server info
    # cdn_host = "40.122.125.188"
    # cdn_host = "aws.cmu-agens.com"
    # cdn_host = "cmu-agens.azureedge.net"
    # get_hop_by_host(cdn_host)
    file_path = os.path.dirname(__file__)
    hop_file = file_path + '/config/all_hops.json'
    get_hop_by_user(hop_file)