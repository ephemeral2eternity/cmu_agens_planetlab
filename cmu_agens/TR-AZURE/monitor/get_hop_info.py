## Do Traceroute to a CDN host and gets detailed info on each hop.
# get_hop_info.py
# Chen Wang, Oct. 23, 2015
# chenw@cmu.edu
import json
import os
from monitor.traceroute import *
from ipinfo.host2ip import *
from ipinfo.ipinfo import *

def read_hop_info(hopinfo_path, hop_ip):
    default_hop_path = hopinfo_path + hop_ip + ".json"
    if os.path.exists(default_hop_path):
        try:
            hop_info = json.load(open(default_hop_path))
        except:
            os.remove(default_hop_path)
            if is_ip(hop_ip):
                hop_info = ipinfo(hop_ip)
                save_ipinfo(hopinfo_path, hop_info)
            else:
                hop_info = {}
    else:
        if not is_ip(hop_ip):
            hop_ip = host2ip(hop_ip)

        if is_ip(hop_ip):
            hop_info = ipinfo(hop_ip)
            save_ipinfo(hopinfo_path, hop_info)
        else:
            hop_info = {}
    return hop_info


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
            hop_info = read_hop_info(hop_data_folder, cur_hop_ip)
            print hop_info
    return hops


if __name__ == "__main__":
    ## Denote the server info
    # cdn_host = "40.122.125.188"
    # cdn_host = "aws.cmu-agens.com"
    cdn_host = "cmu-agens.azureedge.net"
    get_hop_by_host(cdn_host)
    # file_path = os.path.dirname(__file__)
    # hop_file = file_path + '/config/all_hops.json'
    # get_hop_by_user(hop_file)