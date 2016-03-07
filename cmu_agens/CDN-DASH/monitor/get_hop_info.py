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
            node_info = json.load(open(default_hop_path))
            return node_info
        except:
            os.remove(default_hop_path)

    if not is_ip(hop_ip):
        hop_ip = host2ip(hop_ip)

    if is_ip(hop_ip):
        hop_info = ipinfo(hop_ip)
        node_info = {}
        node_info['ip'] = hop_ip
        node_info['name'] = hop_info['hostname']
        node_info['city'] = hop_info['city']
        node_info['region'] = hop_info['region']
        node_info['country'] = hop_info['country']
        node_info['AS'] = hop_info['AS']
        node_info['ISP'] = hop_info['ISP']
        node_info['latitude'] = hop_info['latitude']
        node_info['longitude'] = hop_info['longitude']
    else:
        node_info = {}

    return node_info


def get_node_info(ip):
    hop_data_folder = os.getcwd() + '/hopData/'
    node_info = read_hop_info(hop_data_folder, ip)
    # print hop_info
    save_ipinfo(hop_data_folder, node_info)
    return node_info


def get_hop_by_host(cdn_host):
    hop_data_folder = os.getcwd() + '/hopData/'

    hops = traceroute(cdn_host)
    # print hops

    full_hops = []

    hop_ids = sorted(hops.keys(), key=int)
    for hop_id in hop_ids:
        cur_hop_ip = hops[hop_id]['ip']
        if cur_hop_ip is '*':
            continue

        if not is_reserved(cur_hop_ip):
            node_info = get_node_info(cur_hop_ip)
            if is_ip(node_info['name']):
                node_info['name'] = hops[hop_id]['name']

            save_ipinfo(hop_data_folder, node_info)
            full_hops.append(node_info)

    return full_hops


if __name__ == "__main__":
    ## Denote the server info
    # cdn_host = "40.122.125.188"
    # cdn_host = "aws.cmu-agens.com"
    cdn_host = "cmu-agens.azureedge.net"
    full_hops = get_hop_by_host(cdn_host)
    # file_path = os.path.dirname(__file__)
    # hop_file = file_path + '/config/all_hops.json'
    # get_hop_by_user(hop_file)