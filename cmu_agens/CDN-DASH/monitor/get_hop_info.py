## Do Traceroute to a CDN host and gets detailed info on each hop.
# get_hop_info.py
# Chen Wang, Oct. 23, 2015
# chenw@cmu.edu
import json
import os
from monitor.traceroute import *
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
        if not hop_info['city']:
            node_info['city'] = ""
        else:
            try:
                node_info['city'] = str(hop_info['city'])
            except:
                node_info['city'] = hop_info['city'].encode('utf-8')
        node_info['region'] = str(hop_info['region'])
        node_info['country'] = str(hop_info['country'])
        node_info['AS'] = hop_info['AS']
        try:
            node_info['ISP'] = str(hop_info['ISP'])
        except:
            node_info['ISP'] = hop_info['ISP'].encode('utf-8')
        node_info['latitude'] = hop_info['latitude']
        node_info['longitude'] = hop_info['longitude']
    else:
        node_info = {}

    return node_info


def get_node_info_local(ip):
    filePath = os.path.split(os.path.realpath(__file__))[0]
    parentPath = os.path.split(filePath)[0]
    hop_data_folder = parentPath + '/hopData/'
    node_info = read_hop_info(hop_data_folder, ip)
    # print hop_info
    save_ipinfo(hop_data_folder, node_info)
    return node_info

def get_node_info(ip=None, nodeTyp='router'):
    manager = "manage.cmu-agens.com"
    node_info = get_node_info_from_manager(manager, ip, nodeTyp)
    return node_info

def get_ext_ip_from_websites():
    url = 'http://jsonip.com'

    try:
        resp = requests.get(url)
        ip_info = json.load(resp)
        ext_ip = ip_info["ip"]
    except:
        ext_ip = urllib2.urlopen('http://whatismyip.org').read()
    return ext_ip

# ================================================================================
## Get Client Agent Name
# ================================================================================
def get_ext_ip():
    node_info = get_node_info()
    ext_ip = node_info['ip']
    if not node_info:
        ext_ip = get_ext_ip_from_websites()
        node_info = ipinfo()
    hostname = socket.gethostname()
    if node_info['name'] == node_info['ip']:
        node_info['name'] = hostname
    return ext_ip, node_info

# ================================================================================
# Get the traceroute info from current client to a CDN host
# ================================================================================
def get_hop_by_host(cdn_host):
    # filePath = os.path.split(os.path.realpath(__file__))[0]
    # parentPath = os.path.split(filePath)[0]
    # hop_data_folder = parentPath + '/hopData/'

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
            if (is_ip(node_info['name'])) and ('No Host' not in hops[hop_id]['name']):
                node_info['name'] = hops[hop_id]['name']

            # save_ipinfo(hop_data_folder, node_info)
            full_hops.append(node_info)

    return full_hops


if __name__ == "__main__":
    ## Denote the server info
    # cdn_host = "40.122.125.188"
    # cdn_host = "aws.cmu-agens.com"
    cdn_host = "az.cmu-agens.com"
    full_hops = get_hop_by_host(cdn_host)
    print full_hops
    # file_path = os.path.dirname(__file__)
    # hop_file = file_path + '/config/all_hops.json'
    # get_hop_by_user(hop_file)
