#!/usr/bin/python
### phonehome.py
### Hello World demonstration script
phonehome_url = "http://146.148.66.148:8000/hello/"
import sys, urllib, xmlrpclib, socket

# PlanetLab PLCAPI url
plc_host = 'www.planet-lab.org'
api_url = "https://%s:443/PLCAPI/"%plc_host

## Get PLC_API
plc_api = xmlrpclib.ServerProxy(api_url, allow_none=True)

# Anonymous user to retrieve node name
auth = {}
auth['AuthMethod'] = "anonymous"
auth['Role'] = "user"
hostname = socket.gethostname()
query = plc_api.GetNodes(auth, {'hostname': hostname}, ['site_id'])

site_id = query[0]['site_id']
site_info = plc_api.GetSites(auth, {'site_id': site_id}, ['site_id', 'name', 'url','latitude', 'longitude', 'login_base'])
if isinstance(site_info[0]['name'], unicode):
        site_info[0]['name'] = site_info[0]['name'].encode('utf-8')
site_info = urllib.urlencode(site_info[0])
print site_info
urllib.urlopen(phonehome_url, site_info)
