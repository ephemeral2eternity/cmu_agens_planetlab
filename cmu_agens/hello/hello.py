#!/usr/bin/python
### phonehome.py
### Hello World demonstration script
update_site_url = "http://104.197.6.6:8000/hello/site/"
update_node_url = "http://104.197.6.6:8000/hello/node/"
import sys, urllib, xmlrpclib, socket, subprocess, platform
import random, time
from get_gce_region import *

## Wait a random period to avoid congesting planetlab nodes
def waitRandom(hostname, minPeriod, maxPeriod):
        ## Sleeping a random interval before starting the client agent
        waitingTime = random.randint(minPeriod, maxPeriod)
        print "Before run hello to report node info on %s, sleep %d seconds!" % (hostname, waitingTime)
        time.sleep(waitingTime)

hostname = socket.gethostname()
waitRandom(hostname, 1, 300)

# PlanetLab PLCAPI url
plc_host = 'www.planet-lab.org'
api_url = "https://%s:443/PLCAPI/"%plc_host

## Get PLC_API
plc_api = xmlrpclib.ServerProxy(api_url, allow_none=True)

# Anonymous user to retrieve node name
auth = {}
auth['AuthMethod'] = "anonymous"
auth['Role'] = "user"

query = plc_api.GetNodes(auth, {'hostname': hostname}, ['site_id', 'node_id', 'hostname', 'node_type'])

site_id = query[0]['site_id']
site_info = plc_api.GetSites(auth, {'site_id': site_id}, ['site_id', 'name', 'url','latitude', 'longitude', 'login_base'])
if isinstance(site_info[0]['name'], unicode):
        site_info[0]['name'] = site_info[0]['name'].encode('utf-8')
site_info = urllib.urlencode(site_info[0])
print site_info
urllib.urlopen(update_site_url, site_info)

## Get OS version
p = subprocess.Popen(["cat", "/etc/redhat-release"], stdout=subprocess.PIPE)
os_version = p.stdout.read()
print os_version

## Get Python Version
python_version = "python " + platform.python_version()
print python_version

## Get the zone and region for this client
zone, region = get_gce_region()

node_info = {}
node_info['node_id'] = query[0]['node_id']
node_info['site_id'] = query[0]['site_id']
node_info['hostname'] = query[0]['hostname']
node_info['zone'] = zone
node_info['region'] = region
node_info['node_type'] = query[0]['node_type']
node_info['node_os'] = os_version
node_info['node_python'] = python_version
node_info['node_ip'] = socket.gethostbyname(node_info['hostname'])
node_info = urllib.urlencode(node_info)
print node_info
urllib.urlopen(update_node_url, node_info)
