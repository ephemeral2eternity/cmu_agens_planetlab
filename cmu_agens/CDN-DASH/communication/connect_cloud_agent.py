import urllib2
import json
import os
import socket
from ipinfo.ipinfo import *
from monitor.ping import *

# Get the list of all locators
def get_cloud_agents(manager):
    url = "http://%s/get_cloud_agents/" % manager

    cloud_agents = []
    try:
        req = urllib2.Request(url)
        response = urllib2.urlopen(req)
        data = json.load(response)
        cloud_agents = data
    except:
        print "Failed to get the list of cloud agents! Please initialize the cloud agent list on the manager!"

    return cloud_agents

def get_my_cloud_agent(manager, method="geo"):
    url = "http://%s/client/getLocator?method=%s" % (manager, method)

    my_cloud_agent = {}
    try:
        req = urllib2.Request(url)
        response = urllib2.urlopen(req)
        my_cloud_agent = json.load(response)
    except:
        print "Failed to contact the manager! Please check the status of " + manager + "!"

    if not my_cloud_agent:
        my_cloud_agent = connect_cloud_agent(manager, method)

    return my_cloud_agent


def get_geo_dist(coord1, coord2):
    geo_dist_squre = (coord2[0] - coord1[0])**2 + (coord2[1] - coord1[1])**2
    geo_dist = geo_dist_squre ** 0.5
    return geo_dist


def geo_connect(client_info, cloud_agents):
    client_coords = [float(client_info['latitude']), float(client_info['longitude'])]
    geo_dist_dict = {}
    cloud_agent_ips = {}
    for node in cloud_agents:
        node_name = node['name']
        node_ip = node['ip']
        cloud_agent_ips[node_name] = node_ip
        node_geo_dist = get_geo_dist(client_coords, [float(node['lat']), float(node['lon'])])
        geo_dist_dict[node_name] = node_geo_dist

    connected_cloud_agent = min(geo_dist_dict.items(), key=lambda x:x[1])[0]
    connected_cloud_agent_ip = cloud_agent_ips[connected_cloud_agent]
    return connected_cloud_agent, connected_cloud_agent_ip

def net_connect(cloud_agents):
    net_dist_dict = {}
    cloud_agent_ips = {}
    for node in cloud_agents:
        node_name = node['name']
        node_ip = node['ip']
        cloud_agent_ips[node_name] = node_ip
        rtt = getMnRTT(node_ip)
        net_dist_dict[node_name] = rtt

    connected_cloud_agent = min(net_dist_dict.items(), key=lambda x:x[1])[0]
    connected_cloud_agent_ip = cloud_agent_ips[connected_cloud_agent]
    return connected_cloud_agent, connected_cloud_agent_ip


def notify_manager(manager, method, client_info):
    url = "http://%s/client/add?method=%s" % (manager, method)
    isSuccess = True
    try:
        req = urllib2.Request(url)
        req.add_header('Content-Type', 'application/json')
        response = urllib2.urlopen(req, json.dumps(client_info))
    except:
        isSuccess = False

    return isSuccess


def connect_cloud_agent(manager, method="geo"):
    cloud_agents = get_cloud_agents(manager)
    client_info = ipinfo()
    if not client_info['hostname']:
        client_info['hostname'] = socket.gethostname()
    elif "No" in client_info['hostname']:
        client_info['hostname'] = socket.gethostname()

    if method == "geo":
        connected_cloud_agent, connected_cloud_agent_ip = geo_connect(client_info, cloud_agents)
    elif method == "net":
        connected_cloud_agent, connected_cloud_agent_ip = net_connect(cloud_agents)
    else:
        print "Unknown method to connect to a cloud agent!"
        return None
    ## Post the info the the centralized manager
    client_info['locator'] = connected_cloud_agent

    num_tries = 0
    while (not notify_manager(manager, method, client_info)) and (num_tries < 3):
        num_tries += 1

    if num_tries == 3:
        print "Try to notify the manager 3 times but all failed."

    return {'name' : connected_cloud_agent, 'ip' : connected_cloud_agent_ip}


if __name__ == '__main__':
    manager = "manage.cmu-agens.com"
    my_cloud_agent = get_my_cloud_agent(manager, 'net')
    print "Connected cloud agent: ", my_cloud_agent

